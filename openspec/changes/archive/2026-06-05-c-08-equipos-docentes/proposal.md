## Why

El sistema ya tiene el modelo `Asignacion` (C-07) pero carece de endpoints que lo expongan: los coordinadores no pueden gestionar equipos, los docentes no pueden ver sus propias asignaciones, y el flujo de inicio de cuatrimestre (FL-03) no puede ejecutarse sin asignación masiva ni clonado entre cohortes. Este change cierra esa brecha funcional crítica.

## What Changes

- **Nuevo**: `GET /api/equipos/mis-asignaciones` — vista del docente autenticado sobre sus propias asignaciones activas (F4.2)
- **Nuevo**: `GET /api/equipos/` — listado global de asignaciones del tenant con filtros (F4.3)
- **Nuevo**: `POST /api/equipos/` — alta individual de asignación
- **Nuevo**: `PUT /api/equipos/{id}` — edición de asignación (vigencia, rol, responsable)
- **Nuevo**: `DELETE /api/equipos/{id}` — soft delete de asignación
- **Nuevo**: `POST /api/equipos/asignacion-masiva` — asignación de múltiples docentes a materia × carrera × cohorte × rol en una sola operación (F4.4, RN-30)
- **Nuevo**: `POST /api/equipos/clonar` — clona todas las asignaciones activas de un equipo origen hacia un destino con nuevas fechas de período (F4.5, RN-12)
- **Nuevo**: `PUT /api/equipos/vigencia-masiva` — actualiza fechas desde/hasta de todas las asignaciones de un equipo seleccionado (F4.6)
- **Nuevo**: `GET /api/equipos/exportar` — descarga el equipo completo en formato CSV/XLSX (F4.7)
- **Nuevo**: eventos de auditoría `ASIGNACION_CREAR`, `ASIGNACION_MODIFICAR`, `ASIGNACION_ELIMINAR` para cada operación de escritura
- **Guard**: todos los endpoints de escritura requieren permiso `equipos:asignar` (COORDINADOR, ADMIN); lectura requiere `equipos:ver` o sesión propia

## Capabilities

### New Capabilities

- `equipos-docentes`: endpoints REST sobre el modelo Asignacion — CRUD individual, asignación masiva, clonado entre períodos, modificación masiva de vigencia y exportación del equipo docente

### Modified Capabilities

- `asignaciones`: se agregan requisitos de comportamiento de API sobre el modelo existente — listado con filtros, operaciones masivas y clonado

## Impact

- **Código nuevo**: `backend/app/routers/equipos.py`, `backend/app/services/equipos_service.py`, extensión de `backend/app/repositories/asignacion_repository.py`
- **Sin migración**: el modelo `Asignacion` ya existe desde C-07; no se necesitan nuevas columnas
- **Auditoría**: genera entradas en `AuditLog` para cada mutación, usando el servicio de auditoría de C-05
- **RBAC**: requiere que los permisos `equipos:asignar` y `equipos:ver` estén registrados en el catálogo de la base (ya existe la infraestructura de C-04)
- **Tests**: nuevos tests de integración para cada endpoint, incluyendo casos de clonado entre cohortes, asignación masiva y modificación masiva de vigencia
