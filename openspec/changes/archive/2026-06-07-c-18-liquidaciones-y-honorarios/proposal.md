## Why

activia-trace consolida toda la operación académica pero hoy no liquida los honorarios de su equipo docente. FINANZAS necesita calcular, segmentar y cerrar la remuneración de cada docente por (cohorte × mes) sobre una grilla salarial versionada (Base por rol + Plus por categoría de materia), separar a los docentes que facturan por su propio canal, y dejar todo auditado e inmutable tras el cierre. Cerradas PA-22 (claves de Plus como texto libre, mapeo `categoria_clave` en `Materia`) y PA-23 (acumulación lineal sin tope), el dominio queda desbloqueado para implementarse.

## What Changes

- Se agrega el campo `categoria_clave: str | None` a la entidad `Materia` existente (ALTER TABLE en la migración) — mapeo materia→clave de Plus. NULL → no genera Plus, no bloquea la liquidación (PA-22).
- Nuevos modelos: `SalarioBase` (Base por rol con vigencia), `SalarioPlus` (Plus por grupo×rol con vigencia), `Liquidacion` (resultado por docente/período), `Factura` (comprobantes de docentes facturantes).
- Nuevo cálculo de liquidación por (cohorte × mes): `Total = Base(rol vigente) + Σ(Plus(clave, rol) × N_comisiones_de_esa_clave)`, acumulación lineal sin tope (PA-23, RN-33/34).
- Segmentación contable en tres universos: detalle general (PROFESOR/TUTOR/COORDINADOR), NEXO diferenciado (suma al total), y facturantes excluidos del total (RN-35/36/38, F10.6).
- Cierre inmutable de liquidaciones (RN-22) con auditoría `LIQUIDACION_CERRAR`.
- ABM de la grilla salarial (Base y Plus) con vigencia temporal abierta (RN-31).
- ABM de facturas con estados Pendiente↔Abonada (RN-39).
- Nuevos endpoints `/api/liquidaciones/*` y `/api/facturas/*` bajo guards `liquidaciones:*` y `facturas:gestionar` (rol FINANZAS).

## Capabilities

### New Capabilities
- `liquidaciones-y-honorarios`: cálculo, segmentación, cierre inmutable e historial de liquidaciones por (cohorte × mes) sobre grilla salarial versionada (Base + Plus), gestión de facturas de docentes facturantes y ABM de la grilla salarial.

### Modified Capabilities
<!-- El cambio en Materia (categoria_clave) es aditivo a nivel de schema y no altera requisitos de la capability estructura-academica; se documenta como impacto, no como delta de spec. -->

## Impact

- **Modelos nuevos**: `backend/app/models/{salario_base,salario_plus,liquidacion,factura}.py`.
- **Modelo modificado**: `backend/app/models/materia.py` (+ `categoria_clave`).
- **Migración**: `0017` — crea 4 tablas nuevas + `ALTER TABLE materias ADD COLUMN categoria_clave`.
- **Repositories/Services/Schemas/Routers** nuevos para liquidaciones y facturas.
- **Permisos** ya existentes en `core/permisos.py`: `LIQUIDACIONES_OPERAR`, `LIQUIDACIONES_CERRAR`, `FACTURAS_GESTIONAR`.
- **Dependencias de datos**: lee `Asignacion` (comisiones/rol/cohorte vigentes), `Materia.categoria_clave`, `Usuario.facturador`, `Cohorte`.
- **Governance**: dominio CRÍTICO (liquidaciones) — Strict TDD obligatorio, multi-tenancy row-level, cierre inmutable, auditoría.
