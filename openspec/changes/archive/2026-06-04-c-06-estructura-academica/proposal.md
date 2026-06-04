## Why

El sistema necesita un catálogo de estructura académica (Carrera, Cohorte, Materia) como base para todos los módulos que dependen de ella: comisiones, inscripciones, calificaciones, encuentros y liquidaciones. Sin estas entidades no hay a qué anclar alumnos, docentes ni actividad académica. Este change cierra la deuda fundacional del modelo de datos luego de tener autenticación y RBAC operativos (C-04).

## What Changes

- **Nueva entidad `Carrera`**: catálogo de programas académicos del tenant. ABM completo con soft delete.
- **Nueva entidad `Cohorte`**: camadas de ingreso por carrera y año. ABM completo con soft delete.
- **Nueva entidad `Materia`**: catálogo único de materias del tenant. ABM completo con soft delete.
- **Migración Alembic `0004_estructura_academica`**: crea las tres tablas con índices únicos de unicidad por tenant.
- **Endpoints REST** bajo `/v1/carreras`, `/v1/cohortes`, `/v1/materias`, todos protegidos con `require_permission("estructura:gestionar")`.
- **Permiso `estructura:gestionar`** agregado al catálogo de permisos del sistema.
- **Tests** de unicidad, soft delete y control de acceso (sin permiso → 403).

> **Nota sobre preguntas abiertas**: PA-01 (catálogo de materias vs. instancia de dictado) y PA-07 (cohortes ↔ carrera) están pendientes. Este change implementa el modelo base documentado en `04_modelo_de_datos.md` (Materia como catálogo plano, Cohorte como FK directa a Carrera), que es suficiente para desbloquear C-07 y C-09. La resolución de PA-01 y PA-07 puede agregar entidades adicionales en changes posteriores sin romper este modelo.

## Capabilities

### New Capabilities

- `estructura-academica`: CRUD de Carrera, Cohorte y Materia con multi-tenancy row-level, unicidad por tenant y soft delete.

### Modified Capabilities

- `rbac`: se agrega el permiso `estructura:gestionar` al catálogo de permisos del sistema.

## Impact

- **Backend**: nuevos modelos, repositories, services y routers en `backend/app/`; nueva migración Alembic.
- **Permisos**: `estructura:gestionar` debe existir en la tabla `Permission` para que los endpoints funcionen.
- **Dependencias upstream**: C-07 (comisiones), C-09 (alumnos), C-10 (calificaciones) dependen de Carrera, Cohorte y Materia.
- **Sin impacto en frontend**: no hay UI en este change.
