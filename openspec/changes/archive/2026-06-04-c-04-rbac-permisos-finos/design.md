## Context

C-03 provee `get_current_user` que resuelve `user_id`, `tenant_id` y `roles` (nombres) del JWT. Este change agrega la capa de autorización: traduce esos roles a permisos efectivos, los expone como parte del contexto de usuario, y provee el guard `require_permission` para declarar el permiso requerido por endpoint.

Constraints:
- Permisos como datos en DB (no hardcode en código). El catálogo es administrable por tenant.
- Fail-closed: si el usuario no tiene el permiso explícito en DB → 403. Nunca asumir permiso por defecto.
- Vigencia temporal: `usuario_roles.vig_hasta` acota cuándo el rol está activo; roles vencidos no otorgan permisos.
- Los permisos se resuelven server-side en cada request — nunca se almacenan en el JWT.
- El seed de roles del dominio se aplica en la migración (función Python que inserta las filas base).

## Goals / Non-Goals

**Goals:**
- Modelos `Rol`, `Permiso`, `RolPermiso`, `UsuarioRol` con vigencia temporal.
- Resolución de permisos efectivos: dada una sesión autenticada, calcular la unión de permisos de todos los roles vigentes del usuario en su tenant.
- Guard `require_permission("modulo:accion")` como FastAPI dependency.
- Seed de los 7 roles del dominio + matriz de permisos base.
- `get_current_user` extendido para incluir `permisos_efectivos: set[str]`.
- Migración `0003_rbac` reversible.

**Non-Goals:**
- Permisos `(propio)` con scope de recurso — el scope fino sobre objetos propios vs ajenos se implementa en los services de dominio (C-07+). El RBAC de este change solo distingue si el usuario tiene el permiso global.
- ABM de roles/permisos vía API — el catálogo se gestiona por migración/seed en este change; la API de gestión es una feature posterior.
- Impersonación — C-05.

## Decisions

### D-01: Permisos como strings `modulo:accion` en tabla `permisos`
**Elegido**: Tabla `permisos(id UUID, tenant_id UUID, codigo VARCHAR UNIQUE per tenant, descripcion TEXT)`. El `codigo` es el string `modulo:accion` (ej: `calificaciones:importar`).
**Por qué**: Simple, legible en logs, extensible sin cambiar el esquema. El guard compara strings.
**Alternativa descartada**: Bitmask — no legible, difícil de extender.

### D-02: Roles y permisos son por tenant (no globales)
**Elegido**: `roles.tenant_id` y `permisos.tenant_id` — cada tenant tiene su propio catálogo. El seed crea los roles base para TODOS los tenants existentes al momento de la migración, y un hook/signal los crea para tenants nuevos.
**Nota práctica**: Para el MVP (un tenant de prueba), el seed los crea directamente. La lógica de "crear roles base al crear un tenant" se implementa en el service de Tenant cuando se construya el ABM (C-06+).

### D-03: `UsuarioRol` con vigencia `vig_desde` / `vig_hasta`
**Elegido**: `usuario_roles(id, tenant_id, usuario_id, rol_id, vig_desde DATE, vig_hasta DATE nullable)`. Un rol vencido (`vig_hasta < hoy`) no se incluye en la resolución de permisos.
**Por qué**: Permite rotación natural de docentes entre cuatrimestres sin borrar el histórico (regla de auditoría append-only).

### D-04: Resolución de permisos en `get_current_user` (una query extra por request)
**Elegido**: Al autenticar, se hace una query que une `usuario_roles → rol_permisos → permisos` filtrando por vigencia. El resultado (`set[str]`) se adjunta al objeto `UsuarioAutenticado`.
**Alternativa descartada**: Cache en Redis — dependencia extra no justificada para MVP; los permisos cambian raramente.
**Trade-off**: Una query adicional por cada request protegido. Aceptable para MVP; se puede cachear con TTL corto en el futuro.

### D-05: Guard `require_permission` como dependency de FastAPI
**Elegido**: Función `require_permission(permiso: str)` retorna una dependency de FastAPI que toma el `UsuarioAutenticado` del scope y verifica `permiso in usuario.permisos_efectivos`. Si no → raise `HTTPException(403)`.
**Uso en endpoint**: `@router.get("/...", dependencies=[Depends(require_permission("calificaciones:importar"))])`.
**Fail-closed**: si `permisos_efectivos` es vacío o el permiso no está → 403 inmediato.

### D-06: Seed como función Python en la migración
**Elegido**: La migración `0003_rbac` incluye una función `seed_roles_base(conn)` que inserta los 7 roles y sus permisos usando `INSERT ... ON CONFLICT DO NOTHING` para idempotencia. El `downgrade()` no borra el seed (soft fail — la tabla se dropea de todas formas).

## Risks / Trade-offs

- **[Riesgo] Permisos por tenant duplican el catálogo** → Para el MVP con pocos tenants es negligible. Si escala a cientos de tenants, considerar permisos globales (sistema) + override por tenant.
- **[Trade-off] Query de permisos por request** → Mitigación futura: TTL cache en memoria o Redis. Por ahora aceptable.
- **[Riesgo] Seed no aplicado a tenants creados después de la migración** → Documentado como limitación del MVP; el service de Tenant deberá llamar a `seed_roles_base` al crear un tenant nuevo (C-06+).

## Migration Plan

1. `0003_rbac`: crea `roles`, `permisos`, `rol_permisos`, `usuario_roles`. Luego aplica seed.
2. `downgrade()`: DROP tablas en orden inverso (FK constraints).
3. Aplicar en test con DB efímera antes de correr tests.

## Open Questions

*(ninguna — el scope está completamente definido por la KB y las reglas duras)*
