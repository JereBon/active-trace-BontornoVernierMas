## Why

El sistema necesita poder cargar y versionar el padrón de alumnos habilitados para cada materia×cohorte, ya sea desde archivos `.xlsx`/`.csv` (flujo manual) o sincronizando directamente desde Moodle Web Services (flujo automático nocturno o bajo demanda). Sin esta capacidad, no existe base para importar calificaciones, detectar atrasados ni ejecutar comunicación dirigida a alumnos reales. Es el punto de entrada de todo el flujo académico.

## What Changes

- **Nuevo modelo `VersionPadron`**: registra cada carga de padrón como una versión inmutable. Solo puede haber una versión activa por `(tenant_id, materia_id, cohorte_id)` en simultáneo; activar una nueva desactiva automáticamente la anterior (soft-deactivation, no borrado).
- **Nuevo modelo `EntradaPadron`**: fila por alumno dentro de una versión. El campo `usuario_id` puede ser nulo cuando el alumno aún no tiene cuenta en el sistema.
- **Importación desde archivo** (`POST /padron/importar`): acepta `.xlsx` o `.csv` con columnas nombre, apellidos, email, comisión, regional. Devuelve preview antes de confirmar.
- **Integración Moodle Web Services** (`integrations/moodle_ws.py`): cliente async que consume la API estándar de Moodle para obtener usuarios, inscripciones y actividades. Sync nocturna automática + endpoint on-demand. Errores de conectividad → `502` con política de reintento.
- **Vaciado de padrón** (`DELETE /padron/materia/{materia_id}`): elimina todas las versiones del padrón para la materia del tenant, respetando RN-04 (scope-isolated).
- **Audit log**: toda operación de carga genera evento `PADRON_CARGAR` en la tabla de auditoría.
- **Migración Alembic 0009**: crea tablas `version_padron` y `entrada_padron`.

## Capabilities

### New Capabilities

- `padron-ingesta`: Carga, versionado y gestión del padrón de alumnos por materia×cohorte. Incluye importación desde archivo y sincronización Moodle WS.
- `moodle-integration`: Cliente Moodle Web Services async con sync nocturna, on-demand y manejo de errores 502/reintento.

### Modified Capabilities

_(ninguna — no hay cambios de requisitos en specs existentes)_

## Impact

- **Backend nuevos archivos**: `models/version_padron.py`, `models/entrada_padron.py`, `repositories/padron_repository.py`, `services/padron_service.py`, `routers/padron_router.py`, `integrations/moodle_ws.py`, `migrations/versions/0009_version_padron_entrada_padron.py`
- **Permisos RBAC**: `padron:leer`, `padron:cargar`, `padron:vaciar` — deben registrarse en el catálogo de permisos.
- **Dependencias externas**: `openpyxl` (parseo xlsx), `httpx` (cliente async HTTP para Moodle WS).
- **Configuración por tenant**: URL de Moodle WS y token se almacenan cifrados (AES-256) en la configuración del tenant.
- **Compatibilidad hacia adelante**: `EntradaPadron.usuario_id` nullable permite cargar alumnos antes de que tengan cuenta, y vincularlos luego mediante matching por email.
