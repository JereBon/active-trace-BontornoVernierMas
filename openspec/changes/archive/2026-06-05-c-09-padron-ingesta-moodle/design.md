## Context

C-07 (usuarios-PII) estableció el modelo `Usuario` con cifrado de PII. C-09 construye sobre eso para cargar el padrón de alumnos por materia×cohorte, ya sea desde archivos o desde Moodle WS. No hay aún ningún modelo de padrón en el sistema. La migración anterior es `0008`; ésta es `0009`.

El padrón es el punto de entrada de todo el flujo académico: sin él no hay calificaciones que importar ni alumnos a quienes comunicar. El diseño debe garantizar que cada versión sea inmutable una vez cargada, que solo exista una activa por contexto, y que el cliente Moodle sea reemplazable por el fallback manual sin cambios en el resto del sistema.

## Goals / Non-Goals

**Goals:**
- Modelo versionado de padrón: `VersionPadron` + `EntradaPadron`, ambas con `TenantScopedMixin`.
- Activación de nueva versión desactiva la anterior atómicamente (transacción DB).
- Importación desde `.xlsx` / `.csv` con preview antes de confirmar.
- Cliente Moodle WS async (`moodle_ws.py`) con sync nocturna y on-demand.
- Manejo de errores Moodle → `502` con mecanismo de reintento configurable.
- Vaciado scope-isolated (RN-04): solo las entradas del usuario que ejecuta, en esa materia.
- Audit log `PADRON_CARGAR` en toda operación de carga.
- Permisos RBAC: `padron:leer`, `padron:cargar`, `padron:vaciar`.
- Migración Alembic `0009_version_padron_entrada_padron`.
- Strict TDD: test que falla → código mínimo → triangulación → refactor.

**Non-Goals:**
- Importación de calificaciones (C-10).
- Matching automático entre `EntradaPadron.email` y `Usuario` existente (puede hacerse después).
- UI frontend de carga de padrón (C-21+).
- Sincronización de actividades Moodle (C-10).

## Decisions

### D1 — `VersionPadron.activa` como flag booleano en la tabla, no columna derivada

**Alternativas consideradas**:
- (A) Columna `activa: bool` explícita → elegida.
- (B) Derivar "activa" como `MAX(created_at)` por contexto → requiere window function en cada query; difícil de invalidar parcialmente.

**Rationale**: La activación es un evento de negocio explícito (RN-05 + inversión al activar nueva versión). El flag explícito permite un índice parcial `WHERE activa = true` y simplifica las queries de los repositories. La transición se hace en una transacción: `UPDATE SET activa = false WHERE materia_id = X AND cohorte_id = Y AND activa = true`, luego INSERT de la nueva.

### D2 — `EntradaPadron.usuario_id` nullable

**Rationale**: El dominio permite cargar alumnos antes de que tengan cuenta en el sistema (KB §E6, §04). Forzar FK no-nullable bloquearía el flujo. El matching se hace diferido por email. La FK tiene `ON DELETE SET NULL` para no perder la entrada si el usuario es soft-deleted (soft delete no borra la fila, pero en migraciones futuras podría suceder una purga).

### D3 — PII en `EntradaPadron` cifrada con AES-256

El campo `email` de `EntradaPadron` es PII. Igual que `Usuario.email`, se almacena cifrado usando `app.core.crypto` (AES-256, ya implementado en C-07). El campo `nombre` y `apellidos` son información pública-institucional, no se cifran (decisión pragmática alineada con el modelo `Usuario` existente).

### D4 — Parser de archivos: `openpyxl` + `csv.DictReader`

Se encapsula en `services/padron_parser.py`. El servicio devuelve una lista de DTOs `EntradaPadronRaw` sin persistir nada — el `PadronService` es quien decide confirmar. Esto permite el flujo preview: parsear → devolver preview al cliente → el cliente llama a `/confirmar` o descarta.

### D5 — Cliente Moodle WS como adaptador (`integrations/moodle_ws.py`)

Interfaz: `MoodleWSClient` con métodos `get_enrolled_users(course_id)`, `health_check()`. Implementación usa `httpx.AsyncClient`. Si Moodle devuelve error HTTP o timeout → `MoodleWSError` que el router mapea a `502`. Retry con backoff exponencial: 3 intentos, 1s/2s/4s, solo para errores de red (no 4xx).

El cliente recibe `moodle_url` y `token` como parámetros de construcción (desencriptados en runtime desde la configuración del tenant). Esto permite mockear en tests sin parchear HTTP.

### D6 — Vaciado scope-isolated (RN-04)

`DELETE /padron/materia/{materia_id}` elimina (soft delete: `deleted_at = now()`) todas las `VersionPadron` + `EntradaPadron` del tenant **y del usuario que llama**. El `PadronRepository` filtra siempre por `tenant_id`. El `PadronService` recibe además el `usuario_id` del JWT para el scope de vaciado.

### D7 — Flujo de capas

```
PadronRouter  →  PadronService  →  PadronRepository  →  VersionPadron / EntradaPadron
                      ↓
                PadronParser (archivos)
                MoodleWSClient (Moodle WS)
                AuditLogService (PADRON_CARGAR)
```

Nunca acceso directo a DB desde el router ni desde el servicio.

## Risks / Trade-offs

- [Riesgo] Activación de versión no-atómica si dos requests llegan simultáneamente.
  → Mitigación: `SELECT FOR UPDATE` en la transacción de activación; constraint único parcial en DB (`UNIQUE (tenant_id, materia_id, cohorte_id) WHERE activa = true`).

- [Riesgo] Archivos `.xlsx` con columnas mal nombradas o en orden incorrecto.
  → Mitigación: el parser valida headers en la primera fila; devuelve 422 con lista de columnas faltantes.

- [Riesgo] Moodle WS token expirado o rotado → fallo silencioso en sync nocturna.
  → Mitigación: `health_check()` antes de sync; si falla, se registra en audit log con `PADRON_CARGAR` + `resultado: ERROR_MOODLE` y se notifica al ADMIN del tenant.

- [Trade-off] `EntradaPadron.email` cifrado: no se puede hacer `WHERE email = ?` directamente.
  → Asumido: el matching por email se hace en Python (desencriptar y comparar), no en SQL. Aceptable dado el volumen esperado por materia (<500 alumnos).

## Migration Plan

1. Alembic `0009_version_padron_entrada_padron`:
   - Crear tabla `version_padron` con constraint único parcial `(tenant_id, materia_id, cohorte_id) WHERE activa = true`.
   - Crear tabla `entrada_padron` con FK nullable a `usuarios`.
   - Índices: `(tenant_id, materia_id, cohorte_id)` en `version_padron`; `(version_id, tenant_id)` en `entrada_padron`.

2. Rollback: `downgrade()` hace `DROP TABLE entrada_padron`, `DROP TABLE version_padron` en ese orden.

3. No hay datos previos que migrar (primera carga de padrón).

## Open Questions

- ¿Se debe vincular automáticamente `EntradaPadron.usuario_id` al momento de la carga si ya existe un `Usuario` con el mismo email? Decisión diferida a C-10 o post-lanzamiento para no bloquear esta iteración.
- ¿El vaciado (F1.5) soft-delete las versiones o las borra físicamente? Por consistencia con la regla de auditoría append-only, se usa soft delete.
