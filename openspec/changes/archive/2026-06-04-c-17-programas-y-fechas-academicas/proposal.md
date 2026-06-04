## Why

La plataforma ya tiene estructura académica (materias, cohortes, carreras) pero carece de dos recursos clave que coordinadores y alumnos necesitan para el seguimiento del ciclo lectivo: el programa oficial de cada materia (syllabus) y el calendario de instancias evaluativas (parciales, TPs, coloquios). Sin estos datos, no es posible completar la trazabilidad del alumno ni ofrecer una vista unificada del calendario académico por tenant.

## What Changes

- Nuevo modelo `ProgramaMateria`: asocia un documento de programa oficial a una materia, con referencia a cohorte y carrera, marcando si está vigente y publicado.
- Nuevo modelo `FechaAcademica`: registra instancias evaluativas (parcial, TP, coloquio, recuperatorio) de una materia en un período, con número de instancia y fecha exacta.
- Endpoints REST bajo `/api/programas` para ABM de programas (requiere `estructura:gestionar`).
- Endpoint de consulta `/api/programas/{materia_id}` para obtener los programas de una materia.
- Endpoints REST bajo `/api/fechas-academicas` para ABM de fechas evaluativas (requiere `estructura:gestionar`).
- Migración Alembic `0006_programas_y_fechas_academicas` con ambas tablas.
- Tests: CRUD básico, acceso denegado sin permiso, soft delete y aislamiento multi-tenant.

## Capabilities

### New Capabilities

- `programas-materia`: gestión y consulta de programas oficiales de materias, asociados a tenant, materia, cohorte y carrera.
- `fechas-academicas`: registro y gestión de instancias evaluativas del calendario académico por tenant, materia y cohorte.

### Modified Capabilities

<!-- No se modifica ninguna spec existente. Los modelos de estructura académica (materias, cohortes) solo se referencian via FK. -->

## Impact

- **Backend**: nuevos archivos en `backend/app/models/`, `backend/app/repositories/`, `backend/app/api/routes/`, `backend/app/schemas/`.
- **Base de datos**: nueva migración Alembic `0006_programas_y_fechas_academicas` con dos tablas nuevas.
- **Dependencias**: C-06 (estructura académica — materias, cohortes, carreras deben existir).
- **Permisos**: requiere permiso `estructura:gestionar` ya definido en el sistema RBAC (C-03).
- **Sin breaking changes**: funcionalidad completamente nueva.
