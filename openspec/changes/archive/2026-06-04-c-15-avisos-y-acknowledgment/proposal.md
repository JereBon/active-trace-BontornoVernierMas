## Why

Los actores institucionales (COORDINADOR, ADMIN) necesitan publicar avisos dirigidos a audiencias específicas (todos los usuarios, por rol, o por usuario individual) dentro de un tenant. Sin este módulo, no existe un mecanismo formal para comunicar novedades urgentes ni para requerir confirmación de lectura (*acknowledgment*), lo que impide trazar quién fue notificado y quién confirmó haber leído la información.

## What Changes

- Nuevo modelo `Aviso`: publicación de avisos institucionales con ventana de vigencia, alcance segmentable y soft delete.
- Nuevo modelo `AvisoAck`: registro de confirmación de lectura por usuario, idempotente.
- Endpoint `POST /api/avisos` — crear aviso (requiere permiso `avisos:publicar`).
- Endpoint `GET /api/avisos` — listar avisos vigentes del tenant (cualquier usuario autenticado).
- Endpoint `POST /api/avisos/{id}/ack` — confirmar lectura (requiere permiso `avisos:confirmar`).
- Endpoint `GET /api/avisos/{id}/acks` — ver quiénes confirmaron (requiere `avisos:publicar`).
- Migración Alembic para las tablas `avisos` y `aviso_acks`.

## Capabilities

### New Capabilities

- `avisos`: Publicación y gestión de avisos institucionales con vigencia, alcance por audiencia (TODOS/ROL/USUARIO) y acknowledgment de lectura.

### Modified Capabilities

<!-- No hay specs existentes modificadas -->

## Impact

- **Nuevos archivos**: `backend/app/models/aviso.py`, `backend/app/repositories/aviso_repository.py`, `backend/app/api/v1/avisos.py`, `backend/app/schemas/aviso.py`, migración Alembic.
- **Tests**: `backend/tests/test_avisos.py` cubriendo creación, listado de vigentes, ack idempotente y control de permisos (403).
- **Dependencias**: C-02 (modelos base + tenancy), C-05 (audit_log disponible para registrar acciones), C-06 (estructura académica para scope por materia/cohorte — scope básico TODOS/ROL/USUARIO no bloquea).
- **Governance**: BAJO — CRUD de contenido institucional sin lógica crítica de seguridad.
