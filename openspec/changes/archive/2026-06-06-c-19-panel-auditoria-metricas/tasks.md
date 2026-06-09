## 1. Schemas Pydantic (auditoria.py)

- [x] 1.1 Crear `backend/app/schemas/auditoria.py` con `extra='forbid'` en todos los modelos
- [x] 1.2 Definir `AccionPorDia` (fecha: date, total: int)
- [x] 1.3 Definir `InteraccionDocente` (actor_id: UUID, total: int)
- [x] 1.4 Definir `InteraccionMateria` (actor_id: UUID, materia_id: UUID | None, total: int)
- [x] 1.5 Definir `PanelMetricasOut` (acciones_por_dia, por_docente, por_materia)
- [x] 1.6 Definir `AuditLogOut` (todos los campos de AuditLog)
- [x] 1.7 Definir `LogPaginadoOut` (items: list[AuditLogOut], total: int)
- [x] 1.8 Definir `ComunicacionDocenteOut` (docente_id, pendiente, enviada, fallida, cancelada)

## 2. Repository de auditoría analítica (auditoria_repository.py)

- [x] 2.1 Crear `backend/app/repositories/auditoria_repository.py` — solo lectura, sin heredar de AuditLogRepository
- [x] 2.2 Método `acciones_por_dia(actor_id=None, fecha_desde=None, fecha_hasta=None)` — GROUP BY date_trunc('day', fecha_hora)
- [x] 2.3 Método `interacciones_por_docente(actor_id=None)` — GROUP BY actor_id sobre audit_logs
- [x] 2.4 Método `interacciones_por_materia(actor_id=None)` — GROUP BY actor_id + detalle->>'materia_id'
- [x] 2.5 Método `log_paginado(actor_id=None, fecha_desde=None, fecha_hasta=None, accion=None, limit=200, offset=0)` — retorna (items, total)
- [x] 2.6 Método `comunicaciones_por_docente(docente_id=None)` — consulta tabla comunicaciones GROUP BY docente_id, estado

## 3. Service de auditoría (auditoria_service.py)

- [x] 3.1 Crear `backend/app/services/auditoria_service.py`
- [x] 3.2 Método `get_panel(current_user)` — aplica scope: COORDINADOR pasa `actor_id=current_user.user_id`, ADMIN pasa `actor_id=None`
- [x] 3.3 Método `get_log(current_user, filtros)` — aplica mismo scope; ignora `usuario_id` del request si el rol es COORDINADOR
- [x] 3.4 Método `get_comunicaciones(current_user)` — aplica scope: COORDINADOR pasa `docente_id=current_user.user_id`

## 4. Router de auditoría (auditoria.py)

- [x] 4.1 Crear `backend/app/api/v1/routers/auditoria.py` con prefix `/v1/auditoria`
- [x] 4.2 `GET /panel` — guard `AUDITORIA_VER`, retorna `PanelMetricasOut`
- [x] 4.3 `GET /log` — guard `AUDITORIA_VER`, params: fecha_desde, fecha_hasta, usuario_id, accion, limit, offset; retorna `LogPaginadoOut`
- [x] 4.4 `GET /comunicaciones` — guard `AUDITORIA_VER`, retorna `list[ComunicacionDocenteOut]`

## 5. Registro del router en main.py

- [x] 5.1 Importar `router as auditoria_router` en `backend/app/main.py`
- [x] 5.2 Agregar `application.include_router(auditoria_router)` junto a los demás routers

## 6. Tests TDD (test_auditoria.py)

- [x] 6.1 Safety net: correr tests existentes y capturar baseline
- [x] 6.2 RED — `test_acciones_por_dia_agrupa_correctamente`: crear N logs en mismas fechas, verificar conteo agrupado
- [x] 6.3 GREEN + triangulación — al menos 2 fechas distintas, verificar que cada fecha tiene su conteo correcto
- [x] 6.4 RED — `test_scope_coordinador_solo_ve_propias_acciones`: dos actores, COORDINADOR solo ve las suyas
- [x] 6.5 GREEN + triangulación — verificar que ADMIN ve todas
- [x] 6.6 RED — `test_log_paginado_filtro_fecha`: insertar logs en rango y fuera de rango, verificar filtro
- [x] 6.7 GREEN + triangulación — verificar `limit` y `offset` funcionan correctamente
- [x] 6.8 RED — `test_comunicaciones_por_docente_conteo_por_estado`: insertar comunicaciones con distintos estados
- [x] 6.9 GREEN + triangulación — verificar conteo por estado correcto y scope COORDINADOR
- [x] 6.10 RED — `test_panel_endpoint_403_sin_permiso`: llamar `/panel` sin `auditoria:ver` → 403
- [x] 6.11 GREEN — verificar que con permiso retorna 200
