## Why

El modelo `Usuario` existe con campos de autenticación (C-03), pero carece de los datos de perfil completo (PII): nombre, apellidos, DNI, CUIL, CBU y demás campos sensibles del dominio. Sin la entidad `Asignacion`, el sistema no puede vincular usuarios con roles en contextos académicos concretos, lo que bloquea cualquier flujo RBAC real (importación de calificaciones, comunicaciones, supervisión). Este change cierra esa brecha y habilita C-08 en adelante.

## What Changes

- **Extensión del modelo `Usuario`**: se agregan todos los campos de perfil PII al modelo ya existente — nombre, apellidos, DNI [cifrado], CUIL [cifrado], CBU [cifrado], alias_cbu [cifrado], banco, regional, legajo, legajo_profesional, facturador — con cifrado AES-256 para los campos sensibles.
- **Nuevo modelo `Asignacion`**: vincula Usuario ↔ rol ↔ contexto académico (materia_id, carrera_id, cohorte_id, comisiones) con vigencia (desde/hasta) y jerarquía (responsable_id).
- **ABM de usuarios** protegido con `require_permission("usuarios:gestionar")`: crear, leer, actualizar, desactivar (soft delete). Nunca hard delete.
- **Endpoint `GET /api/me`**: devuelve el perfil propio del usuario autenticado (sin permiso especial).
- **Migración Alembic** `0006_usuarios_pii_asignaciones`: agrega columnas PII a `usuarios` y crea tabla `asignaciones`.
- **Tests**: PII cifrada en DB, perfil propio vía `/api/me`, usuario sin permiso → 403, vigencia de asignación bloquea permisos.

## Capabilities

### New Capabilities

- `usuarios-perfil`: Gestión del perfil completo del usuario (PII cifrada, legajos, datos bancarios) y endpoint de perfil propio.
- `asignaciones`: Vinculación de usuarios con roles en contextos académicos con vigencia temporal.

### Modified Capabilities

- `usuarios-auth`: El modelo `Usuario` se extiende con campos de perfil PII; el contrato de auth no cambia pero el schema de respuesta del perfil crece.

## Impact

- **Backend models**: `backend/app/models/usuario.py` (extensión), nuevo `backend/app/models/asignacion.py`
- **Backend repositories**: `backend/app/repositories/usuario.py`, nuevo `backend/app/repositories/asignacion.py`
- **Backend routers/services**: nuevos endpoints `/api/users` y `/api/me`, nuevo servicio de asignaciones
- **Migración**: `backend/alembic/versions/0006_usuarios_pii_asignaciones.py`
- **Crypto**: uso de `backend/app/core/crypto.py` (ya implementado en C-02) para cifrado/descifrado PII
- **Tests**: `backend/tests/test_usuarios.py`, `backend/tests/test_asignaciones.py`
- **Dependencias**: requiere C-06 (estructura académica: modelos Materia, Carrera, Cohorte) para las FK de Asignacion
