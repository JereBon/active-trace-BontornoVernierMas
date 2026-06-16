## Context

Con RBAC operativo (C-04), el sistema puede aplicar control de acceso fino a los endpoints. El siguiente bloque fundacional es el catálogo de estructura académica: Carrera, Cohorte y Materia. Estos objetos son referencias que todos los módulos upstream (comisiones C-07, alumnos C-09, calificaciones C-10) necesitan para funcionar.

Existen dos preguntas abiertas relevantes (PA-01, PA-07) que podrían ampliar el modelo en el futuro, pero no bloquean este change: se implementa el modelo base documentado en `04_modelo_de_datos.md` y se lo diseña para ser extensible.

## Goals / Non-Goals

**Goals:**
- Modelos SQLAlchemy para Carrera, Cohorte y Materia con tenant isolation row-level.
- Repositorios con scope de tenant por defecto.
- Services con validación de unicidad y soft delete.
- Routers REST protegidos con `require_permission("estructura:gestionar")`.
- Migración Alembic `0004_estructura_academica`.
- Tests de unicidad, soft delete y acceso denegado.

**Non-Goals:**
- Relación Materia ↔ Carrera/Cohorte (entidad Asignación, E5): queda para C-07.
- InstanciaDictado o cualquier resolución de PA-01: change posterior.
- UI / frontend.
- Importación masiva desde Moodle.

## Decisions

### D1 — Una migración, tres tablas
Se crea `0004_estructura_academica.py` con las tablas `carreras`, `cohortes` y `materias` en un solo script. Alternativa: una migración por tabla. Se elige una sola porque las tres tablas forman un bloque lógico cohesivo y se despliegan juntas; no tiene sentido aplicarlas de forma parcial.

### D2 — Soft delete con `deleted_at` (heredado de BaseModel)
Se usa el patrón ya establecido en el proyecto (`deleted_at IS NULL` para registros activos). El campo `estado` (Activa/Inactiva) es distinto del soft delete: una carrera inactiva sigue existiendo y puede reactivarse; una carrera borrada (soft) desaparece de todas las vistas. Los repositorios filtran `deleted_at IS NULL` y `tenant_id` por defecto.

### D3 — Enum `EstadoEntidad` compartido
`Activa` / `Inactiva` es el mismo dominio para las tres entidades. Se define un único `enum EstadoEntidad` en `backend/app/models/base.py` (o en un módulo de enums compartidos) para evitar duplicación.

### D4 — Permiso único `estructura:gestionar`
Todos los endpoints (crear, leer, actualizar, desactivar) de las tres entidades comparten el permiso `estructura:gestionar`. Esto simplifica la configuración de roles iniciales. Si en el futuro se necesita granularidad (ej. `estructura:leer` sin `gestionar`), se puede agregar sin romper lo existente.

### D5 — Paginación simple en listados
Los endpoints de listado devuelven `limit` / `offset` configurable (default 50). No se implementa cursor-based pagination en este change.

### D6 — Número de migración
C-05 (audit-log) corre en paralelo. Si C-05 usa `0004`, C-06 usa `0005`. Se verifica en runtime antes de crear el archivo. Al momento de diseño, `backend/alembic/versions/` contiene solo `0001`, `0002`, `0003`, por lo que se reserva `0004` para este change.

## Risks / Trade-offs

- **PA-01 y PA-07 no resueltas** → El modelo base (`Materia` plana, `Cohorte` con FK directa a `Carrera`) podría requerir migraciones aditivas cuando se resuelvan. Mitigación: diseñar tablas sin FKs entre Materia y Carrera/Cohorte hasta que E5 (Asignación) se implemente.
- **Conflicto de número de migración con C-05** → Si C-05 corre en paralelo y usa `0004`, hay colisión. Mitigación: verificar el directorio antes de crear el archivo; si `0004` existe, usar `0005`.
- **Cohorte sin unicidad fuerte** → El par `(tenant_id, carrera_id, nombre)` es único pero `nombre` es texto libre; errores de tipeo generan duplicados. Mitigación: documentar y dejar validación de negocio en el service.

## Migration Plan

1. Ejecutar `alembic upgrade head` al desplegar.
2. Insertar permiso `estructura:gestionar` en la tabla `permissions` (puede ser parte de la migración o de un seed).
3. Rollback: `alembic downgrade -1` elimina las tres tablas (CASCADE seguro ya que no hay FKs que apunten a ellas en este change).

## Open Questions

- **PA-01**: ¿`Materia` del catálogo vs. `InstanciaDictado`? — Pospuesto. Se implementa `Materia` plana.
- **PA-07**: ¿`Cohorte` exclusiva de una `Carrera`? — Se asume FK directa por ahora; si se vuelve N:M se agrega tabla de relación en change posterior.
