## ADDED Requirements

### Requirement: Role and permission catalog stored as data
The system SHALL store roles (`Rol`), permissions (`Permiso`), and role-permission mappings (`RolPermiso`) in the database as administrable data per tenant. Permissions SHALL use the format `modulo:accion` (e.g., `calificaciones:importar`). No permission logic SHALL be hardcoded.

#### Scenario: Roles and permissions exist in database after seed
- **WHEN** the migration `0003_rbac` is applied to an empty database with an existing tenant
- **THEN** the 7 domain roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) exist in the `roles` table for that tenant, and all their permissions exist in `permisos` and `rol_permisos`

#### Scenario: Permission catalog is extensible without code changes
- **WHEN** a new permission row is inserted into `permisos` and linked to a role via `rol_permisos`
- **THEN** users with that role immediately gain the new permission on their next request (no deploy required)

---

### Requirement: User role assignment with temporal validity
The system SHALL support assigning one or more roles to a user via `UsuarioRol`, each with a `vig_desde` (start date) and optional `vig_hasta` (end date). A role assignment is active only if `vig_hasta IS NULL OR vig_hasta >= today`.

#### Scenario: Active role assignment grants permissions
- **WHEN** a user has a role assignment with `vig_hasta IS NULL`
- **THEN** that role's permissions are included in the user's effective permissions

#### Scenario: Expired role assignment does not grant permissions
- **WHEN** a user has a role assignment where `vig_hasta < today`
- **THEN** that role's permissions are NOT included in the user's effective permissions

#### Scenario: Multiple roles yield union of permissions
- **WHEN** a user has two active role assignments (e.g., PROFESOR and COORDINADOR)
- **THEN** their effective permissions are the union of both roles' permissions

---

### Requirement: Effective permissions resolved server-side per request
On every authenticated request, the system SHALL resolve the user's effective permissions by querying `usuario_roles → rol_permisos → permisos`, filtered by tenant and active assignments. The result SHALL be attached to the authenticated user context. Permissions SHALL never be stored in the JWT.

#### Scenario: Effective permissions reflect current DB state
- **WHEN** a user's role assignment is revoked in the database (vig_hasta set to yesterday)
- **THEN** on the next request the user no longer has that role's permissions (no cache invalidation needed)

---

### Requirement: require_permission guard enforces authorization — fail-closed
The `require_permission("modulo:accion")` FastAPI dependency SHALL verify that the authenticated user's effective permissions include the declared permission. If the permission is absent, the response SHALL be HTTP 403. Without an explicit permission grant in the database, access SHALL be denied (fail-closed).

#### Scenario: User with permission accesses protected endpoint
- **WHEN** a user with `calificaciones:importar` in their effective permissions calls an endpoint guarded by `require_permission("calificaciones:importar")`
- **THEN** the response is HTTP 200 (or whatever the endpoint returns)

#### Scenario: User without permission receives 403
- **WHEN** a user without `calificaciones:importar` calls an endpoint guarded by `require_permission("calificaciones:importar")`
- **THEN** the response is HTTP 403

#### Scenario: Unauthenticated request returns 401 before reaching permission check
- **WHEN** a request without a valid Bearer token is made to a guarded endpoint
- **THEN** the response is HTTP 401 (from get_current_user, before the permission check)

---

### Requirement: get_current_user includes effective permissions
The `get_current_user` dependency SHALL return a `UsuarioAutenticado` object that includes `permisos_efectivos: set[str]` alongside `user_id`, `tenant_id`, and `roles`.

#### Scenario: Authenticated user has permisos_efectivos populated
- **WHEN** a valid Bearer token is used on any request
- **THEN** `get_current_user` returns a user object with a non-None `permisos_efectivos` set (may be empty if user has no active roles)

---

### Requirement: Domain roles seeded with base permission matrix
The migration SHALL seed the 7 domain roles and their permissions according to the base matrix from the knowledge base. The seed SHALL be idempotent (`INSERT ... ON CONFLICT DO NOTHING`).

#### Scenario: Seed is idempotent
- **WHEN** the seed function is run twice on the same database
- **THEN** no duplicate rows are created and no error is raised
