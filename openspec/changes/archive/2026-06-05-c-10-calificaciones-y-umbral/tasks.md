## 1. Migración y modelos

- [x] 1.1 Crear `app/models/calificacion.py` con modelo `Calificacion` (TenantScopedMixin: `id`, `tenant_id`, `entrada_padron_id`, `materia_id`, `actividad`, `nota_numerica`, `nota_textual`, `aprobado`, `origen`, `importado_at`)
- [x] 1.2 Crear `app/models/umbral_materia.py` con modelo `UmbralMateria` (`id`, `tenant_id`, `asignacion_id`, `materia_id`, `umbral_pct` default 60, `valores_aprobatorios` ARRAY/JSON)
- [x] 1.3 Registrar ambos modelos en `app/models/__init__.py`
- [x] 1.4 Crear migración Alembic `0010_calificacion_umbral_materia.py` que crea tablas `calificacion` y `umbral_materia` con constraints e índices

## 2. Lógica de derivación (TDD primero)

- [x] 2.1 Escribir tests para `calcular_aprobado(nota_numerica, nota_textual, umbral_pct, valores_aprobatorios)`: 5 escenarios del spec (numérica ≥ umbral, numérica < umbral, textual aprobatoria, textual no aprobatoria, numérica == umbral exacto)
- [x] 2.2 Implementar función `calcular_aprobado` en `app/services/calificacion_service.py` (o módulo de utilidades de dominio)

## 3. Parser de archivo LMS (TDD primero)

- [x] 3.1 Escribir tests para `CalificacionParser.parse_preview(file_bytes, filename)`: detección de columnas `(Real)`, detección de textuales, error si falta `Email address`
- [x] 3.2 Implementar `app/services/calificacion_parser.py` con `CalificacionParser`: método `parse_preview` que devuelve `{actividades_numericas, actividades_textuales, alumnos_preview}`, basado en el patrón de `padron_parser.py`
- [x] 3.3 Escribir tests para `CalificacionParser.parse_actividades_seleccionadas(file_bytes, filename, actividades)`: filtra solo las actividades seleccionadas
- [x] 3.4 Implementar `parse_actividades_seleccionadas` en el parser

## 4. Repository de calificaciones (TDD primero)

- [x] 4.1 Escribir tests para `CalificacionRepository`: `upsert_bulk`, `list_by_materia`, `delete_by_asignacion_materia`; todos con tenant isolation
- [x] 4.2 Implementar `app/repositories/calificacion_repository.py` con `CalificacionRepository(TenantScopedRepository)`:
  - `upsert_bulk(tenant_id, calificaciones: list[Calificacion])` — ON CONFLICT DO UPDATE
  - `list_by_materia(tenant_id, materia_id)` → list[Calificacion]
  - `delete_by_asignacion_materia(tenant_id, asignacion_id, materia_id)` (para vaciado, scope-isolated per RN-04)
- [x] 4.3 Escribir tests para `UmbralMateriaRepository`: `get_by_asignacion_materia`, `upsert`
- [x] 4.4 Implementar `UmbralMateriaRepository` (puede ir en el mismo archivo o en `umbral_materia_repository.py`): `get_by_asignacion_materia`, `upsert`

## 5. Service de calificaciones (TDD primero)

- [x] 5.1 Escribir tests para `CalificacionService.importar`: flujo completo (parse → calcular_aprobado → upsert_bulk → audit_log), incluyendo test de upsert (re-importar misma actividad actualiza en lugar de duplicar)
- [x] 5.2 Implementar `CalificacionService.importar(tenant_id, actor_id, materia_id, asignacion_id, file_bytes, filename, actividades_seleccionadas)` en `app/services/calificacion_service.py`
- [x] 5.3 Escribir tests para `CalificacionService.configurar_umbral`: crear nuevo umbral, actualizar existente, recálculo de `aprobado` en calificaciones existentes, aislamiento entre docentes
- [x] 5.4 Implementar `CalificacionService.configurar_umbral(tenant_id, actor_id, asignacion_id, materia_id, umbral_pct, valores_aprobatorios)`: upsert de `UmbralMateria` + recálculo batch

## 6. Router y schemas (TDD de integración primero)

- [x] 6.1 Escribir tests de integración para `POST /api/v1/materias/{materia_id}/calificaciones/preview`: responde 200 con actividades detectadas, 422 sin columna requerida
- [x] 6.2 Escribir tests de integración para `POST /api/v1/materias/{materia_id}/calificaciones/importar`: importa, audita, re-importa hace upsert
- [x] 6.3 Escribir tests de integración para `PUT /api/v1/materias/{materia_id}/calificaciones/umbral`: crea, actualiza, aislamiento entre docentes
- [x] 6.4 Crear schemas Pydantic en `app/schemas/calificacion.py`: `CalificacionPreviewResponse`, `ImportarCalificacionesRequest`, `UmbralMateriaRequest`, `UmbralMateriaResponse` (todos con `extra='forbid'`)
- [x] 6.5 Implementar `app/routers/calificaciones.py` con los 3 endpoints; identidad siempre desde JWT; `require_permission("calificaciones:importar")` en import, `require_permission("calificaciones:umbral")` en umbral
- [x] 6.6 Registrar el router en `app/main.py`

## 7. Verificación final

- [x] 7.1 Ejecutar `python -m pytest tests/test_calificaciones.py -v` — todos los tests pasan (54/54)
- [x] 7.2 Verificar cobertura ≥ 80 % líneas y ≥ 90 % reglas de negocio (derivación + umbral + tenant isolation)
- [x] 7.3 Confirmar que la migración 0010 aplica limpiamente: tablas calificacion y umbral_materia creadas por create_all en test setup
