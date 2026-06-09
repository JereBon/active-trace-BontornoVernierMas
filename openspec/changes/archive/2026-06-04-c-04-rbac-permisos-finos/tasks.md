## 1. Modelos RBAC

- [x] 1.1 Crear `backend/app/models/rol.py`: modelo `Rol` (hereda `Base` + `TenantScopedMixin`). Columnas: `codigo` VARCHAR NOT NULL, `nombre` VARCHAR NOT NULL, `descripcion` TEXT nullable. Índice único `(tenant_id, codigo)`.
- [x] 1.2 Crear `backend/app/models/permiso.py`: modelo `Permiso` (hereda `Base` + `TenantScopedMixin`). Columnas: `codigo` VARCHAR NOT NULL (formato `modulo:accion`), `descripcion` TEXT nullable. Índice único `(tenant_id, codigo)`.
- [x] 1.3 Crear `backend/app/models/rol_permiso.py`: tabla de asociación `RolPermiso` (`id` UUID PK, `tenant_id` UUID, `rol_id` UUID FK → roles, `permiso_id` UUID FK → permisos, `created_at`). Índice único `(rol_id, permiso_id)`.
- [x] 1.4 Crear `backend/app/models/usuario_rol.py`: modelo `UsuarioRol` (hereda `Base` + `TenantScopedMixin`). Columnas: `usuario_id` UUID FK → usuarios NOT NULL, `rol_id` UUID FK → roles NOT NULL, `vig_desde` DATE NOT NULL, `vig_hasta` DATE nullable.
- [x] 1.5 Registrar los 4 modelos en `backend/app/models/__init__.py`

## 2. Migración Alembic 0003

- [x] 2.1 Crear `backend/alembic/versions/0003_rbac.py`: `upgrade()` crea tablas `roles`, `permisos`, `rol_permisos`, `usuario_roles` con todos los índices y FK constraints
- [x] 2.2 Implementar función `seed_roles_base(conn)` dentro de la migración: inserta los 7 roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) y los permisos de la matriz `03_actores_y_roles.md §3.3` usando `INSERT ... ON CONFLICT DO NOTHING`
- [x] 2.3 Llamar a `seed_roles_base` al final de `upgrade()` para todos los tenants existentes
- [x] 2.4 Implementar `downgrade()`: DROP tablas en orden inverso (usuario_roles, rol_permisos, permisos, roles)
- [x] 2.5 Verificar `alembic upgrade head` y `alembic downgrade -1` en DB efímera

## 3. Permisos del dominio — catálogo completo

- [x] 3.1 Crear `backend/app/core/permisos.py`: módulo con constantes string para todos los permisos del dominio (ej: `CALIFICACIONES_IMPORTAR = "calificaciones:importar"`). Sirve como referencia para el código y el seed.
- [x] 3.2 Lista completa de permisos a definir según la matriz:
  - `academico:ver_propio` (ALUMNO)
  - `evaluaciones:reservar` (ALUMNO)
  - `avisos:confirmar` (todos los roles)
  - `calificaciones:importar` (PROFESOR, COORDINADOR, ADMIN)
  - `atrasados:ver` (TUTOR, PROFESOR, COORDINADOR, ADMIN)
  - `entregas:ver_sin_corregir` (TUTOR, PROFESOR, COORDINADOR, ADMIN)
  - `comunicacion:enviar` (PROFESOR, COORDINADOR, ADMIN)
  - `comunicacion:aprobar` (COORDINADOR, ADMIN)
  - `encuentros:gestionar` (TUTOR, PROFESOR, COORDINADOR, ADMIN)
  - `guardias:registrar` (TUTOR, PROFESOR, COORDINADOR, ADMIN)
  - `tareas:gestionar` (PROFESOR, COORDINADOR, ADMIN)
  - `avisos:publicar` (COORDINADOR, ADMIN)
  - `equipos:asignar` (COORDINADOR, ADMIN)
  - `estructura:gestionar` (ADMIN)
  - `usuarios:gestionar` (ADMIN)
  - `auditoria:ver` (COORDINADOR, ADMIN, FINANZAS)
  - `liquidaciones:operar` (FINANZAS)
  - `liquidaciones:cerrar` (FINANZAS)
  - `facturas:gestionar` (FINANZAS)
  - `tenant:configurar` (ADMIN)
  - `impersonacion:usar` (ADMIN)

## 4. Repositories RBAC

- [x] 4.1 Crear `backend/app/repositories/rol.py`: `RolRepository(BaseRepository[Rol])` con método `get_by_codigo(codigo: str) -> Rol | None`
- [x] 4.2 Crear `backend/app/repositories/permiso.py`: `PermisoRepository(BaseRepository[Permiso])` con método `get_by_codigo(codigo: str) -> Permiso | None`
- [x] 4.3 Crear `backend/app/repositories/usuario_rol.py`: `UsuarioRolRepository` con método `get_permisos_efectivos(usuario_id: UUID) -> set[str]` — query que une usuario_roles → rol_permisos → permisos filtrando por vigencia (`vig_hasta IS NULL OR vig_hasta >= today`)

## 5. Core RBAC — resolución y guard

- [x] 5.1 Crear `backend/app/core/rbac.py`: función `require_permission(permiso: str) -> Callable` que retorna una FastAPI dependency. La dependency verifica `permiso in current_user.permisos_efectivos`; si no → raise `HTTPException(status_code=403, detail="Forbidden")`
- [x] 5.2 El guard debe ser usable como: `dependencies=[Depends(require_permission("modulo:accion"))]` en cualquier router

## 6. Extender get_current_user con permisos efectivos

- [x] 6.1 Crear/actualizar `backend/app/core/schemas.py` (o equivalente): dataclass/Pydantic `UsuarioAutenticado` con campos `user_id: UUID`, `tenant_id: UUID`, `roles: list[str]`, `permisos_efectivos: set[str]`
- [x] 6.2 Actualizar `get_current_user` en `backend/app/core/dependencies.py`: tras verificar el JWT, hacer query de permisos efectivos via `UsuarioRolRepository.get_permisos_efectivos` y adjuntarlos al objeto retornado

## 7. Tests RBAC (TDD estricto)

- [x] 7.1 Crear `backend/tests/test_rbac.py` con fixtures: tenant, usuario con rol PROFESOR, usuario con rol COORDINADOR, usuario sin roles, endpoint de prueba guardado con `require_permission`
- [x] 7.2 Test RED→GREEN: usuario con permiso correcto → HTTP 200 en endpoint guardado
- [x] 7.3 Test RED→GREEN: usuario sin el permiso → HTTP 403
- [x] 7.4 Test RED→GREEN: usuario con dos roles activos → permisos_efectivos es la unión de ambos roles
- [x] 7.5 Test RED→GREEN: rol con `vig_hasta` vencida → no otorga permisos (HTTP 403 en endpoint que antes pasaba)
- [x] 7.6 Test RED→GREEN: seed idempotente — correr seed dos veces no duplica filas
- [x] 7.7 Triangulación: usuario sin roles → `permisos_efectivos` vacío → HTTP 403 en cualquier endpoint guardado

## 8. Verificación final

- [x] 8.1 Correr `pytest backend/tests/` — todos los tests pasan
- [x] 8.2 Verificar `alembic upgrade head` → `alembic downgrade -1` en DB efímera
- [x] 8.3 Ningún archivo supera 500 LOC
