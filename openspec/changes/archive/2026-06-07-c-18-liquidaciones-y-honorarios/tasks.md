## 1. Modelos y migración

- [ ] 1.1 Crear modelo `SalarioBase` (tenant_id via mixin, rol, monto Numeric, desde Date, hasta Date nullable) en `backend/app/models/salario_base.py`
- [ ] 1.2 Crear modelo `SalarioPlus` (grupo, rol, descripcion, monto Numeric, desde, hasta nullable) en `backend/app/models/salario_plus.py`
- [ ] 1.3 Crear modelo `Liquidacion` (cohorte_id FK, periodo, usuario_id FK, rol, comisiones ARRAY(Text), monto_base, monto_plus, total, es_nexo, excluido_por_factura, estado) en `backend/app/models/liquidacion.py`
- [ ] 1.4 Crear modelo `Factura` (usuario_id FK, periodo, detalle, referencia_archivo, tamano_kb Numeric, estado, cargada_at, abonada_at nullable) en `backend/app/models/factura.py`
- [ ] 1.5 Agregar campo `categoria_clave: str | None` a `Materia` (`backend/app/models/materia.py`)
- [ ] 1.6 Registrar los nuevos modelos en `backend/app/models/__init__.py`
- [ ] 1.7 Crear migración Alembic `0017` que crea las 4 tablas nuevas + `ALTER TABLE materias ADD COLUMN categoria_clave`, con downgrade que revierte ambos

## 2. Repositories (I/O con scope de tenant)

- [ ] 2.1 `SalarioBaseRepository` (CRUD + `get_vigente(rol, periodo)`) en `backend/app/repositories/salario_base.py`
- [ ] 2.2 `SalarioPlusRepository` (CRUD + `get_vigente(grupo, rol, periodo)`) en `backend/app/repositories/salario_plus.py`
- [ ] 2.3 `LiquidacionRepository` (crear, listar por cohorte+periodo, historial cerradas, cerrar, get) en `backend/app/repositories/liquidacion.py`
- [ ] 2.4 `FacturaRepository` (CRUD + filtros estado/usuario/periodo, cambiar estado) en `backend/app/repositories/factura.py`
- [ ] 2.5 Helper en `LiquidacionRepository` para obtener asignaciones docentes vigentes de una cohorte+periodo con su `Materia.categoria_clave`

## 3. Lógica de cálculo (Strict TDD — función pura primero)

- [ ] 3.1 Util pura de período: normalizar `AAAA-MM` a inicio/fin de mes y predicado de vigencia, con tests
- [ ] 3.2 Función pura `_calcular_montos(asignaciones_por_clave, base_rol, plus_por_clave)` → (monto_base, monto_plus, total) con acumulación lineal; tests: 2 comisiones PROG → 2×Plus, claves distintas, materia sin clave
- [ ] 3.3 `LiquidacionService.calcular(cohorte_id, periodo)` que arma registros por docente: base vigente, plus acumulado, es_nexo, excluido_por_factura; tests con base vigente correcta entre múltiples vigencias

## 4. Services (orquestación + auditoría)

- [ ] 4.1 `LiquidacionService.cerrar(...)` — transición Abierta→Cerrada, rechaza si ya Cerrada (error 409/422), emite `audit_action("LIQUIDACION_CERRAR")`; tests de inmutabilidad
- [ ] 4.2 `LiquidacionService.vista_periodo(cohorte_id, periodo)` — segmenta general/NEXO/facturantes + KPIs `total_sin_factura`/`total_con_factura`; tests de segmentación y KPIs
- [ ] 4.3 `LiquidacionService.historial(filtros)` — liquidaciones cerradas filtradas por cohorte/periodo
- [ ] 4.4 `SalarioGrillaService` (ABM Base y Plus) con scope de tenant
- [ ] 4.5 `FacturaService` (ABM + cambio de estado Pendiente↔Abonada, setea `abonada_at`); tests

## 5. Schemas Pydantic v2 (`extra='forbid'`)

- [ ] 5.1 Schemas de Base y Plus (Create/Update/Out) en `backend/app/schemas/salario.py`
- [ ] 5.2 Schemas de Liquidacion (Out, vista segmentada con KPIs, request calcular/cerrar) en `backend/app/schemas/liquidacion.py`
- [ ] 5.3 Schemas de Factura (Create, Out, EstadoUpdate) en `backend/app/schemas/factura.py`

## 6. Routers (HTTP only, guards RBAC)

- [ ] 6.1 Router `/v1/liquidaciones` con guards `liquidaciones:operar` / `liquidaciones:cerrar`: GET `/`, POST `/calcular`, POST `/{id}/cerrar`, GET `/historial`, GET+POST+PUT `/grilla/base`, GET+POST+PUT `/grilla/plus`
- [ ] 6.2 Router `/v1/facturas` con guard `facturas:gestionar`: GET `/`, POST `/`, PATCH `/{id}/estado`
- [ ] 6.3 Registrar ambos routers en el agregador de la API v1
- [ ] 6.4 Tests de endpoint: 403 sin permiso, 409/422 al modificar liquidación cerrada, aislamiento multi-tenant (tenant A no ve B)

## 7. Verificación final

- [ ] 7.1 Correr toda la suite de tests del módulo y confirmar verde (≥90% reglas de negocio)
- [ ] 7.2 Verificar que cada archivo backend ≤500 LOC y componentes/funciones cumplen reglas duras
- [ ] 7.3 Confirmar que la migración 0017 aplica y revierte limpiamente
