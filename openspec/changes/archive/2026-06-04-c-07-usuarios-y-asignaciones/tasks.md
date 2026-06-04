## 1. Migración Alembic

- [x] 1.1 Verificar número libre en `backend/alembic/versions/` y crear `0006_usuarios_pii_asignaciones.py`
- [x] 1.2 Agregar columnas PII a tabla `usuarios`: nombre, apellidos, dni_cifrado, cuil_cifrado, cbu_cifrado, alias_cbu_cifrado, banco, regional, legajo, legajo_profesional, facturador (todas nullable)
- [x] 1.3 Crear tabla `asignaciones` con columnas: id, tenant_id, usuario_id, rol, materia_id (nullable FK), carrera_id (nullable FK), cohorte_id (nullable FK), comisiones (TEXT[]), responsable_id (nullable FK → usuarios), desde, hasta (nullable), deleted_at (soft delete)
- [x] 1.4 Agregar índices: `(tenant_id, usuario_id)` en asignaciones, `(tenant_id, email_hash)` ya existente en usuarios

## 2. Modelo SQLAlchemy — Usuario (extensión)

- [x] 2.1 Agregar columnas PII al modelo `Usuario` en `backend/app/models/usuario.py`: nombre, apellidos, dni_cifrado, cuil_cifrado, cbu_cifrado, alias_cbu_cifrado, banco, regional, legajo, legajo_profesional, facturador
- [x] 2.2 Actualizar `backend/app/models/__init__.py` para exportar el modelo actualizado

## 3. Modelo SQLAlchemy — Asignacion (nuevo)

- [x] 3.1 Crear `backend/app/models/asignacion.py` con modelo `Asignacion`: id (UUID PK), tenant_id, usuario_id (FK), rol (Enum), materia_id (nullable FK), carrera_id (nullable FK), cohorte_id (nullable FK), comisiones (ARRAY), responsable_id (nullable FK), desde, hasta, deleted_at
- [x] 3.2 Agregar `Asignacion` al `backend/app/models/__init__.py`

## 4. Schemas Pydantic

- [x] 4.1 Crear `backend/app/schemas/usuario.py` con: `UsuarioCreate`, `UsuarioUpdate`, `UsuarioResponse` (con PII en texto plano, sin ciphertext), `UsuarioListItem`. Todos con `extra='forbid'`.
- [x] 4.2 Crear `backend/app/schemas/asignacion.py` con: `AsignacionCreate`, `AsignacionResponse`. Todos con `extra='forbid'`.

## 5. Repository — Usuario

- [x] 5.1 Crear `backend/app/repositories/usuario.py` con `UsuarioRepository`: métodos `create`, `get_by_id`, `get_by_email_hash`, `list_by_tenant`, `update`, `deactivate` (soft delete via estado=Inactivo)
- [x] 5.2 El repositorio aplica `crypto.encrypt` en todos los campos PII antes de persistir y `crypto.decrypt` al leer
- [x] 5.3 Todos los métodos filtran por `tenant_id` por defecto

## 6. Repository — Asignacion

- [x] 6.1 Crear `backend/app/repositories/asignacion.py` con `AsignacionRepository`: métodos `create`, `get_vigentes_by_usuario` (filtra `hasta IS NULL OR hasta >= today`), `list_by_usuario`
- [x] 6.2 Todos los métodos filtran por `tenant_id` por defecto

## 7. Service — Usuario

- [x] 7.1 Crear `backend/app/services/usuario.py` con `UsuarioService`: orquesta repositorio, no accede directamente a DB. Métodos: `crear_usuario`, `obtener_usuario`, `actualizar_usuario`, `desactivar_usuario`, `listar_usuarios`, `obtener_perfil_propio`

## 8. Router — Usuarios y Perfil

- [x] 8.1 Crear `backend/app/routers/usuarios.py` con endpoints:
  - `POST /api/users` → require_permission("usuarios:gestionar")
  - `GET /api/users` → require_permission("usuarios:gestionar")
  - `GET /api/users/{id}` → require_permission("usuarios:gestionar")
  - `PUT /api/users/{id}` → require_permission("usuarios:gestionar")
  - `PUT /api/users/{id}/deactivate` → require_permission("usuarios:gestionar")
  - `GET /api/me` → solo autenticado, sin permiso especial
- [x] 8.2 Registrar el router en `backend/app/main.py`

## 9. Tests — TDD

- [x] 9.1 Crear `backend/tests/test_usuarios_pii.py`: test RED primero (PII cifrada en DB — leer la columna cruda y verificar que no es texto plano), luego GREEN implementando el repositorio
- [x] 9.2 Triangular con segundo caso: PII descifrada en response (el JSON de respuesta contiene el valor legible, no el ciphertext)
- [x] 9.3 Crear test para `GET /api/me`: identidad derivada del JWT, responde 401 si no autenticado
- [x] 9.4 Crear test para RBAC en usuarios: usuario sin `usuarios:gestionar` → 403 en `POST /api/users`
- [x] 9.5 Crear `backend/tests/test_asignaciones.py`: test vigencia — asignación vencida no otorga acceso (403), asignación vigente otorga acceso (200)
- [x] 9.6 Test de aislamiento multi-tenant: usuario del tenant A no ve usuarios del tenant B en `GET /api/users`
