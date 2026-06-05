## 1. Migration y modelo

- [x] 1.1 Verificar si `Calificacion` tiene campo `finalizado_lms`; si no existe, crear `backend/alembic/versions/0012_add_finalizado_lms_calificacion.py` con `ALTER TABLE calificacion ADD COLUMN finalizado_lms BOOLEAN NOT NULL DEFAULT FALSE`
- [x] 1.2 Agregar `finalizado_lms: Mapped[bool]` a `backend/app/models/calificacion.py` con `default=False`, `nullable=False`
- [x] 1.3 Ejecutar `alembic upgrade head` en el entorno de test y verificar que la migración aplica sin error

## 2. AnalisisRepository (TDD RED → GREEN)

- [x] 2.1 Escribir test RED: `test_list_calificaciones_por_version` — verifica que el repositorio devuelve solo calificaciones de la versión de padrón activa del tenant
- [x] 2.2 Implementar `AnalisisRepository.list_calificaciones_por_version(materia_id, version_id)` en `backend/app/repositories/analisis_repository.py` — green
- [x] 2.3 Triangular: test con dos tenants distintos — cada tenant solo ve sus propias calificaciones
- [x] 2.4 Escribir test RED: `test_list_sin_corregir` — verifica que solo devuelve calificaciones con `finalizado_lms=True`, `nota_textual=NULL`, `nota_numerica=NULL`
- [x] 2.5 Implementar `AnalisisRepository.list_sin_corregir(materia_id)` — green + triangulación
- [x] 2.6 Escribir test RED: `test_list_alumnos_con_calificaciones_monitor` — verifica filtros por `materia_id`, `comision`, `regional`, `solo_atrasados`, `fecha_desde`/`fecha_hasta`
- [x] 2.7 Implementar `AnalisisRepository.list_monitor(materia_ids, filtros)` — green + triangulación con múltiples filtros combinados

## 3. AnalisisService (TDD RED → GREEN)

- [x] 3.1 Escribir test RED: `test_calcular_atrasados` — alumno sin calificaciones aparece como atrasado con todas las actividades del conjunto como faltantes
- [x] 3.2 Implementar función pura `calcular_atrasados(entradas, calificaciones_por_entrada)` en `backend/app/services/analisis_service.py` — green
- [x] 3.3 Triangular: alumno con todas aprobadas NO aparece; alumno con nota_aprobado=False aparece; alumno con actividades faltantes aparece
- [x] 3.4 Escribir test RED: `test_calcular_ranking` — solo alumnos con ≥1 aprobada, ordenados desc por cantidad
- [x] 3.5 Implementar `calcular_ranking(calificaciones_por_entrada)` — green + triangulación (empate ordena por apellidos)
- [x] 3.6 Escribir test RED: `test_calcular_notas_finales` — promedio simple de nota_numerica; null si no hay numéricas
- [x] 3.7 Implementar `calcular_notas_finales(entradas, calificaciones_por_entrada)` — green + triangulación
- [x] 3.8 Escribir test RED: `test_calcular_reporte_materia` — todos los campos en cero si sin calificaciones
- [x] 3.9 Implementar `calcular_reporte_materia(entradas, calificaciones)` — green + triangulación con datos reales

## 4. Schemas Pydantic

- [x] 4.1 Crear `backend/app/schemas/analisis.py` con schemas de respuesta: `AtrasadoOut`, `RankingItemOut`, `NotaFinalOut`, `MonitorItemOut`, `ReporteMateriaOut`, `SinCorregirOut` — todos con `model_config = ConfigDict(extra='forbid')`
- [x] 4.2 Verificar que los schemas rechazan campos extra (test unitario de schema)

## 5. Router y endpoints

- [x] 5.1 Crear `backend/app/routers/analisis.py` con prefijo `/api/analisis` y `tags=["analisis"]`
- [x] 5.2 Implementar `GET /api/analisis/atrasados?materia_id=` — guard `atrasados:ver`, llama a `AnalisisService.get_atrasados`
- [x] 5.3 Implementar `GET /api/analisis/ranking?materia_id=` — guard `atrasados:ver`, llama a `AnalisisService.get_ranking`
- [x] 5.4 Implementar `GET /api/analisis/notas-finales?materia_id=` — guard `atrasados:ver`, llama a `AnalisisService.get_notas_finales`
- [x] 5.5 Implementar `GET /api/analisis/reporte-materia?materia_id=` — guard `atrasados:ver`, llama a `AnalisisService.get_reporte`
- [x] 5.6 Implementar `GET /api/analisis/sin-corregir?materia_id=` — guard `atrasados:ver`, llama a `AnalisisService.get_sin_corregir`
- [x] 5.7 Implementar `GET /api/analisis/monitor` con query params opcionales (`materia_id`, `comision`, `regional`, `alumno_nombre`, `solo_atrasados`, `fecha_desde`, `fecha_hasta`, `limit`, `offset`) — guard `atrasados:ver`
- [x] 5.8 Registrar el router en `backend/app/main.py` (o el archivo de inclusión de routers del proyecto)

## 6. Tests de integración (endpoints)

- [x] 6.1 Escribir test de integración para `GET /api/analisis/atrasados` — sin permiso → 403; con permiso y datos → lista correcta
- [x] 6.2 Escribir test de integración para `GET /api/analisis/ranking` — solo alumnos con ≥1 aprobada
- [x] 6.3 Escribir test de integración para `GET /api/analisis/sin-corregir` — solo textual sin nota + finalizado_lms=True
- [x] 6.4 Escribir test de integración para `GET /api/analisis/monitor` — filtros por `solo_atrasados` y `materia_id` funcionan correctamente
- [x] 6.5 Escribir test de integración para `GET /api/analisis/reporte-materia` — devuelve ceros sin datos
- [x] 6.6 Ejecutar suite completa: `python -m pytest tests/test_analisis.py -v --tb=short` — 48/48 PASSED

## 7. Verificación final

- [x] 7.1 Confirmar que ningún archivo supera 500 LOC (repo: 297, svc: 323, router: 246, schemas: 99)
- [x] 7.2 Confirmar que `AnalisisService` no contiene ninguna query SQL directa (solo llamadas a `AnalisisRepository`)
- [x] 7.3 Marcar el change `c-11-analisis-atrasados-reportes` como completado en `CHANGES.md`
