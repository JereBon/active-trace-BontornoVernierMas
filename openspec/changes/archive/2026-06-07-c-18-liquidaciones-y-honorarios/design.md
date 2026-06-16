## Context

C-18 implementa el módulo de liquidaciones y honorarios (Épica 10, E17–E20, RN-21/22/31–40). El stack es FastAPI async + SQLAlchemy 2.0 async + Pydantic v2 + Alembic + PostgreSQL, con Clean Architecture estricta (Routers → Services → Repositories → Models). Las dependencias C-04 (RBAC `require_permission`), C-05 (`audit_action`), C-06 (`Materia`, `Cohorte`) y C-07 (`Usuario`, `Asignacion`) ya están implementadas. Las preguntas abiertas PA-22 y PA-23 están cerradas. Governance: CRÍTICO → Strict TDD obligatorio.

Estado actual relevante del código:
- `Usuario` ya tiene `facturador: bool | None` (modalidad de cobro). NO existe `excluido_por_factura` ni `modalidad_cobro` como campos separados.
- `Asignacion` tiene `rol`, `cohorte_id`, `materia_id`, `comisiones: list[str]`, `desde`/`hasta` (vigencia derivada: `hasta IS NULL OR hasta >= hoy`).
- `Materia` NO tiene `categoria_clave` todavía.
- Permisos `LIQUIDACIONES_OPERAR`, `LIQUIDACIONES_CERRAR`, `FACTURAS_GESTIONAR` ya existen en `core/permisos.py`.
- Las acciones de auditoría se definen como constantes `_ACCION_*` a nivel de módulo en cada service (no hay archivo central).
- Migraciones existentes hasta `0016`. La nueva es `0017`.

## Goals / Non-Goals

**Goals:**
- Modelar Base, Plus, Liquidación y Factura con multi-tenancy row-level y soft delete.
- Calcular liquidaciones por (cohorte × mes) con la fórmula cerrada de PA-23.
- Segmentar contablemente (general / NEXO / facturantes) y exponer KPIs.
- Cierre inmutable auditado.
- ABM de grilla salarial y de facturas.

**Non-Goals:**
- Frontend (lo cubre un change de UI posterior).
- Exportación a PDF/contabilidad externa (solo se modela `referencia_archivo`).
- Pago real / integración bancaria.
- Resolver la semántica de PA-25 (rol NEXO) más allá de su tratamiento contable diferenciado ya definido en RN-36.

## Decisions

### D1 — `facturador` existente como fuente de la modalidad de cobro
El task menciona `excluido_por_factura` y `modalidad_cobro` en `Usuario`, pero el modelo real ya tiene `facturador: bool | None`. Reutilizamos `Usuario.facturador` como flag de facturante (evita migración redundante sobre `usuarios`). `Liquidacion.excluido_por_factura` se deriva en el cálculo: `excluido_por_factura = bool(usuario.facturador)`. Alternativa descartada: agregar otra columna a `usuarios` → duplicaría semántica y rompería el modelo de C-07.

### D2 — Origen de comisiones, rol y clave para el cálculo
Las comisiones de un docente en una cohorte+período provienen de `Asignacion` vigente (`cohorte_id` coincide, `desde <= fin_de_mes` y vigencia abierta o `hasta >= inicio_de_mes`). El `rol` de liquidación es `Asignacion.rol`. La clave de Plus de cada comisión se resuelve vía `Asignacion.materia_id → Materia.categoria_clave`. Una asignación sin `materia_id` o con materia de `categoria_clave = NULL` aporta al Base pero no genera Plus. Alternativa descartada: tabla de mapeo comisión→clave separada → PA-22 lo cierra como campo en `Materia`.

### D3 — Cálculo en el Service, queries en el Repository
`LiquidacionService.calcular(cohorte_id, periodo)` orquesta: pide al repo las asignaciones vigentes de la cohorte, agrupa por docente, resuelve Base y Plus vigentes (repo de grilla), aplica la fórmula y persiste registros `Liquidacion`. Toda la aritmética (agrupación por clave, acumulación, suma) es lógica pura testeable en el service. Los repos solo hacen I/O con scope de tenant. La fórmula pura se aísla en una función `_calcular_montos(...)` para test unitario directo.

### D4 — Vigencia de Base/Plus por período AAAA-MM
El período es texto `AAAA-MM`. Para comparar contra `desde`/`hasta` (tipo `date`), se normaliza el período al primer día del mes (`AAAA-MM-01`) y se considera vigente un registro si `desde <= fin_de_mes AND (hasta IS NULL OR hasta >= inicio_de_mes)`. Se asume a lo sumo un registro vigente por (rol) en Base y por (grupo, rol) en Plus en un instante (RN-31); si hubiera solape, se toma el de `desde` más reciente (determinístico).

### D5 — Inmutabilidad de liquidación cerrada
`estado` ∈ {Abierta, Cerrada} (string, patrón `EstadoEntidad`-like). El service rechaza con error de dominio (mapeado a 409/422) cualquier `cerrar`, recálculo o mutación sobre un registro ya Cerrado. El cierre opera a nivel de período (cohorte × mes): cierra todos los registros Abiertos de ese período y emite `audit_action(accion="LIQUIDACION_CERRAR", ...)`. Alternativa descartada: borrar y recrear → viola RN-22 y append-only.

### D6 — Segmentación y KPIs en la vista (no persistidos)
La vista `GET /api/liquidaciones/` arma los tres segmentos (general, NEXO, facturantes) y los KPIs `total_sin_factura` / `total_con_factura` en memoria a partir de los registros del período. No se persisten agregados: se derivan siempre de las filas `Liquidacion` para evitar desincronización. `total_sin_factura` = Σ total de registros con `excluido_por_factura = false` (incluye NEXO). `total_con_factura` = Σ total de registros con `excluido_por_factura = true`.

### D7 — Migración 0017 única
Una sola migración crea `salario_base`, `salario_plus`, `liquidaciones`, `facturas` (todas con columnas de `TenantScopedMixin`) y ejecuta `ALTER TABLE materias ADD COLUMN categoria_clave VARCHAR NULL`. `comisiones` en `Liquidacion` es `ARRAY(Text)` (consistente con `Asignacion.comisiones`). Montos: `Numeric` (decimal), nunca float.

### D8 — Schemas Pydantic v2 con `extra='forbid'`
Todos los DTOs request/response llevan `model_config = ConfigDict(extra='forbid')`. PII no aplica aquí (los montos no son PII), pero `referencia_archivo` es solo una referencia, no contenido del archivo.

## Risks / Trade-offs

- [Solape de vigencias en la grilla] → mitigación: regla determinística "desde más reciente gana" (D4) + el ABM no impide solapes pero el cálculo es estable.
- [Período como texto AAAA-MM vs fechas date] → mitigación: normalización explícita a primer/último día del mes en una util pura testeada.
- [Recalcular un período ya parcialmente cerrado] → mitigación: el cálculo solo (re)genera registros Abiertos; si el período tiene registros Cerrados, el service rechaza recálculo (D5).
- [`Usuario.facturador` es nullable] → mitigación: `bool(facturador)` trata NULL como no-facturante (relación de dependencia por defecto).

## Migration Plan

1. Crear modelos nuevos + agregar `categoria_clave` a `Materia`.
2. Generar migración `0017` (manual, una sola) con las 4 tablas + ALTER TABLE.
3. Implementar repos/services/schemas/routers bajo Strict TDD.
4. Registrar routers en el agregador de la API v1.
5. Rollback: `downgrade` elimina las 4 tablas y dropea la columna `categoria_clave`.

## Open Questions

- Ninguna bloqueante. PA-22 y PA-23 están cerradas. La semántica profunda de NEXO (PA-25) no afecta este cálculo: NEXO se trata como un rol más con Base/Plus propios y segmento diferenciado.
