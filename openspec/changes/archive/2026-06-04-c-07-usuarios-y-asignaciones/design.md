## Context

El modelo `Usuario` fue creado en C-03 con los campos de autenticación: `email_cifrado`, `email_hash`, `password_hash`, `totp_secret`, `totp_activo`, `estado`, `ultimo_acceso`. Los campos de perfil PII (nombre, apellidos, DNI, CUIL, CBU, etc.) no existen aún. La entidad `Asignacion` (E5 del modelo de datos) tampoco existe, lo que impide vincular usuarios con roles y contextos académicos.

Este change opera sobre dominio CRÍTICO: PII cifrada, multi-tenancy y RBAC. Toda decisión de diseño debe priorizar seguridad y auditoría por encima de conveniencia.

## Goals / Non-Goals

**Goals:**
- Extender `usuario` con columnas PII todas cifradas con AES-256 via `crypto.py`
- Crear tabla `asignaciones` con vigencia y FK opcionales a materia/carrera/cohorte
- Exponer ABM de usuarios protegido por `usuarios:gestionar`
- Exponer `GET /api/me` para perfil propio (solo autenticado)
- Migración Alembic numerada `0006_usuarios_pii_asignaciones`
- Tests con DB real siguiendo Strict TDD

**Non-Goals:**
- Gestión de roles/permisos en catálogo (es parte de C-04, ya completado)
- Creación de comisiones o cohortes (C-06)
- Endpoint de listado/gestión de asignaciones (puede venir en C-08)
- Importación masiva de usuarios (C-07 solo cubre ABM individual)

## Decisions

### D1: Extender el modelo existente, no crear uno nuevo

El modelo `Usuario` ya existe en `backend/app/models/usuario.py`. Se agregan columnas PII como columnas nullable de la tabla `usuarios`. Esto preserva la identidad de autenticación existente y evita un JOIN por cada operación.

**Alternativa descartada**: Tabla separada `usuario_perfil`. Agrega complejidad sin beneficio: el perfil y la identidad son el mismo objeto de dominio.

### D2: Cifrado via `crypto.encrypt` / `crypto.decrypt` en el repositorio

El cifrado y descifrado ocurre en la capa Repository, no en el modelo ni en el servicio. El modelo almacena el valor ya cifrado (ciphertext); el repositorio aplica `encrypt` antes de `INSERT/UPDATE` y `decrypt` al leer. Los schemas Pydantic de response nunca exponen el ciphertext.

**Rationale**: mantener la lógica criptográfica en un único punto (repository) simplifica auditoría y facilita rotación de clave.

### D3: `email_hash` para búsquedas, `email_cifrado` para display

El campo `email_hash` (SHA-256, ya implementado) es el índice de búsqueda. `email_cifrado` es el almacenamiento del valor real. Los endpoints que reciben email como criterio de búsqueda deben hashear antes de consultar.

### D4: `estado_vigencia` de Asignacion es derivado, no almacenado

Según E5 del modelo de datos, `estado_vigencia` es un campo calculado (Vigente si `hasta IS NULL OR hasta >= today`). No se persiste. El repositorio de asignaciones aplica este filtro al evaluar permisos efectivos.

### D5: FK opcionales en Asignacion

`materia_id`, `carrera_id`, `cohorte_id` son nullable. Un usuario ADMIN puede tener una asignación sin contexto académico específico (alcance de tenant). Un PROFESOR siempre tiene `materia_id`.

### D6: Soft delete en usuarios

`estado = Inactivo` (soft delete). Nunca se borra un registro. El endpoint de desactivación hace `PUT /api/users/{id}/deactivate` → `estado = Inactivo`. Los repositorios filtran `estado = Activo` por defecto en listados.

## Risks / Trade-offs

- **[Riesgo] Columnas nullable en la extensión** → Las columnas PII se agregan como nullable para no romper registros existentes de auth. Migración segura con `ALTER TABLE ... ADD COLUMN ... NULL`. El código de aplicación debe tolerar `None` en estos campos.
- **[Riesgo] FK a Materia/Carrera/Cohorte de C-06** → Si C-06 no está aplicado, la migración falla por FK faltantes. Mitigación: la migración referencia las tablas de C-06; se debe aplicar después de C-06.
- **[Riesgo] Exposición accidental de PII** → Los schemas Pydantic de response deben definir explícitamente qué campos se incluyen. Nunca exponer campos `*_cifrado`. Tests deben verificar que la respuesta JSON no contiene ciphertext.

## Migration Plan

1. Verificar número libre: `ls backend/alembic/versions/` — usar `0006_`.
2. Crear migración: `alembic revision --autogenerate -m "usuarios_pii_asignaciones"` y editar manualmente para asegurar orden de columnas y constraints.
3. `alembic upgrade head` en entorno de test antes de merge.
4. Rollback: `alembic downgrade -1` (drop columns PII + drop table asignaciones).

## Open Questions

- OQ-1: ¿El campo `facturador` (boolean) es parte de este change o de liquidaciones (C-18)? Decisión tomada: incluirlo aquí porque es un atributo del perfil del usuario, no de una liquidación específica.
- OQ-2: ¿`comisiones` en Asignacion es `ARRAY[text]` o tabla de unión? Decisión: columna `comisiones TEXT[]` (PostgreSQL array) para simplicidad en esta fase; puede normalizarse en C-06 si es necesario.
