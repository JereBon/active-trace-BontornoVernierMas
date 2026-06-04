## Context

El sistema ya cuenta con la estructura académica base (C-06): modelos de `Materia`, `Cohorte`, `Carrera` y `Tenant`. Los permisos RBAC (`estructura:gestionar`) fueron definidos en C-03. Este change agrega dos nuevas entidades de segundo nivel que referencian esa estructura sin modificarla.

El stack sigue el patrón establecido: FastAPI routers → services → repositories → SQLAlchemy models. Las columnas de PII no aplican aquí (no hay datos sensibles de persona).

## Goals / Non-Goals

**Goals**:
- Modelo `ProgramaMateria` con soft delete y aislamiento por tenant.
- Modelo `FechaAcademica` con enum de tipo evaluativo y soft delete.
- Endpoints CRUD completos con control de acceso (`estructura:gestionar`).
- Migración Alembic con número correlativo correcto (0006).
- Tests con DB real, Strict TDD, cobertura ≥80%.

**Non-Goals**:
- Almacenamiento efectivo de archivos (solo se guarda la referencia URL).
- Vista de calendario visual (frontend, fuera de scope de este change).
- Generación de fragmento LMS (F5.4 adicional, deferido).
- Integración Moodle.

## Decisions

### D1: FechaAcademica como entidad propia vs campo en Materia

**Decisión**: entidad propia (`fecha_academica` tabla).  
**Razón**: múltiples instancias evaluativas por materia × cohorte × período. Normalizar evita arrays y permite queries simples por tipo/fecha.  
**Alternativa descartada**: JSONB en la fila de materia — dificulta consultas y validaciones individuales.

### D2: Enum de tipo evaluativo

**Decisión**: `TipoEvaluacion` con valores `PARCIAL`, `TP`, `COLOQUIO`, `RECUPERATORIO`.  
**Razón**: coincide con el dominio definido en E15 del modelo de datos. Enum de Python mapeado a tipo nativo Postgres.  
**Alternativa descartada**: campo texto libre — pierde consistencia en reportes y filtros.

### D3: archivo_url en ProgramaMateria como texto nullable

**Decisión**: `referencia_archivo: str | None` — texto plano, nullable.  
**Razón**: el servicio de almacenamiento (S3/R2) es externo; la plataforma solo guarda la referencia. El upload real es responsabilidad de un change posterior de integración de archivos.  
**Nota**: `vigente` (bool) y `publicado_en` (datetime nullable) permiten control de visibilidad sin necesidad de hard delete.

### D4: Soft delete

**Decisión**: columna `deleted_at: datetime | None` en ambas tablas, igual que el patrón existente (C-02).  
**Razón**: auditoría append-only, regla dura del proyecto.

### D5: Número de migración

**Decisión**: `0006_programas_y_fechas_academicas.py`.  
**Razón**: la última migración existente es `0005_estructura_academica.py`. La siguiente en la secuencia es 0006.

## Risks / Trade-offs

- [Riesgo] `materia_id` / `cohorte_id` / `carrera_id` referencian tablas de C-06. Si C-06 no está aplicado en el entorno de test, la migración fallará.  
  → Mitigación: el conftest de tests levanta todas las migraciones en orden; C-06 precede a esta.

- [Riesgo] El campo `referencia_archivo` no valida que la URL sea accesible.  
  → Mitigación: validación de formato URL en Pydantic; la disponibilidad real se delega al servicio de archivos.

## Migration Plan

1. Ejecutar `alembic upgrade head` en el entorno de destino.
2. Las tablas `programa_materia` y `fecha_academica` se crean vacías; no hay datos a migrar.
3. Rollback: `alembic downgrade -1` elimina las dos tablas sin impacto en datos existentes.

## Open Questions

Ninguna. El scope está cerrado y no depende de preguntas abiertas pendientes (PA-01, PA-07 afectan estructura académica pero no las entidades nuevas de este change).
