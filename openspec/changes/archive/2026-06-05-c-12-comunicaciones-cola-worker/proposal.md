## Why

La plataforma puede detectar alumnos atrasados (C-11) pero no tiene forma de comunicarse con ellos desde el sistema. Para cerrar el ciclo de acompañamiento académico, se necesita una capa de mensajería saliente con cola asíncrona, gestión de estados auditables y un mecanismo de aprobación configurable por tenant que evite envíos masivos no supervisados.

## What Changes

- **Nuevo modelo `Comunicacion`**: entidad E21 del KB, con destinatario cifrado (AES-256-GCM), `lote_id` para agrupación de envíos masivos, máquina de estados `Pendiente → Enviando → Enviado | Error | Cancelado` (RN-15), y `deleted_at` para soft delete.
- **Migración 0013**: tabla `comunicaciones` con todos los campos del modelo, índices por `tenant_id`, `lote_id` y `estado`.
- **Worker asíncrono** (`backend/workers/comunicacion_worker.py`): consume la cola de mensajes en estado `Pendiente`, transiciona a `Enviando` durante el despacho, y finaliza en `Enviado` o `Error`. Plantillas de mensaje con variables de sustitución (`{{nombre}}`, `{{materia}}`, etc.).
- **Preview obligatorio** (F3.1, RN-16): endpoint que renderiza el asunto y cuerpo con variables resueltas antes de encolar. El envío sólo puede iniciarse tras confirmación explícita del usuario.
- **Envío masivo con cola** (F3.2): endpoint para encolar un lote de mensajes a múltiples destinatarios, agrupados por `lote_id`. Guard `comunicacion:enviar`.
- **Aprobación configurable por tenant** (F3.3, RN-17): lotes masivos que superan el umbral del tenant requieren aprobación explícita (`comunicacion:aprobar`) antes de pasar a `Enviando`. Aprobación o cancelación disponible a nivel de lote e individual.
- **API REST** `/api/comunicaciones/*`: endpoints para preview, encolado, aprobación, cancelación y seguimiento de estado.
- **Auditoría** `COMUNICACION_ENVIAR` en cada despacho (y `COMUNICACION_APROBAR` / `COMUNICACION_CANCELAR` para acciones de aprobación).

## Capabilities

### New Capabilities

- `comunicaciones`: Cola de comunicaciones salientes — modelo, máquina de estados, worker asíncrono, preview, envío masivo, aprobación por tenant, API REST y auditoría (E21, F3.1–F3.3, RN-15–17, FL-02 pasos 7-8, FL-04).

### Modified Capabilities

_(ninguna — las capacidades existentes no cambian sus requisitos)_

## Impact

- **Nuevos archivos**: `backend/app/models/comunicacion.py`, `backend/app/repositories/comunicacion_repository.py`, `backend/app/services/comunicacion_service.py`, `backend/app/routers/comunicaciones.py`, `backend/app/schemas/comunicacion.py`, `backend/workers/comunicacion_worker.py`, `backend/alembic/versions/0013_comunicacion.py`, `tests/test_comunicaciones.py`.
- **Dependencias existentes usadas**: `backend/app/core/crypto.py` (AES-256-GCM para `destinatario`), `backend/app/core/audit.py` (audit_action), `backend/app/core/permissions.py` (guards `comunicacion:enviar` y `comunicacion:aprobar`).
- **Sin cambios de schema en tablas existentes**: esta migración sólo agrega la nueva tabla `comunicaciones`.
- **Dependencia de C-11**: el análisis de atrasados provee la lista de alumnos a comunicar; C-12 consume esa salida para el flujo masivo.
