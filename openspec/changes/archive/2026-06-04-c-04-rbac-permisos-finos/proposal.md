## Why

C-03 estableció autenticación: sabemos quién es el usuario y su tenant. Sin RBAC, no hay forma de controlar qué puede hacer ese usuario. C-04 introduce el sistema de autorización fino: catálogo administrable de roles y permisos (`modulo:accion`), la matriz rol×permiso como datos (no hardcode), el guard `require_permission` inyectable en endpoints, y el seed de los 7 roles del dominio. Sin esto, ningún endpoint de dominio puede protegerse — C-05 y todos los changes subsiguientes dependen de este guard.

## What Changes

- Tablas `roles`, `permisos`, `rol_permisos` (catálogo administrable por tenant, no hardcode).
- Seed inicial de los 7 roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) y sus permisos `modulo:accion` según la matriz de `03_actores_y_roles.md §3.3`.
- Tabla `usuario_roles` (asignación de roles a usuarios, con `vig_desde` / `vig_hasta` para vigencia temporal).
- Resolución de permisos efectivos server-side: unión de permisos de todos los roles vigentes del usuario en el tenant actual.
- Dependency/guard `require_permission("modulo:accion")` para FastAPI: verifica que el usuario autenticado tiene el permiso declarado; sin él → HTTP 403. **Fail-closed**: sin permiso explícito en la DB → 403.
- Migración Alembic `0003_rbac`.
- Tests: usuario sin permiso → 403, unión de roles (dos roles = unión de permisos), vigencia (rol vencido no otorga acceso), catálogo administrable (permisos en DB no hardcoded).

## Capabilities

### New Capabilities

- `rbac`: Modelos Rol/Permiso/RolPermiso/UsuarioRol, resolución de permisos efectivos, guard `require_permission`, seed de roles del dominio.

### Modified Capabilities

- `auth`: Se extiende `get_current_user` para incluir los permisos efectivos resueltos del usuario en cada request.

## Impact

- **Nuevo**: `backend/app/models/rol.py`, `backend/app/models/permiso.py`, `backend/app/models/usuario_rol.py`.
- **Nuevo**: `backend/app/repositories/rol.py`, `backend/app/repositories/permiso.py`.
- **Nuevo**: `backend/app/core/rbac.py` (resolución de permisos + guard).
- **Nuevo**: `backend/alembic/versions/0003_rbac.py` + seed SQL/función de seed.
- **Modificado**: `backend/app/core/dependencies.py` — `get_current_user` enriquecido con permisos efectivos.
- **Nuevo**: `backend/tests/test_rbac.py`.
- Todos los changes de dominio (C-05 en adelante) usarán `require_permission` en sus endpoints.
