## ADDED Requirements

### Requirement: Tenant model exists as isolation root
The system SHALL have a `Tenant` entity as the root of all data isolation. Every domain entity SHALL reference a `Tenant` via `tenant_id`.

#### Scenario: Tenant record can be created
- **WHEN** a new `Tenant` is created with a unique slug and name
- **THEN** it is persisted with a UUID primary key, `activo=True`, and timestamps `created_at`/`updated_at` auto-set

#### Scenario: Tenant slug is unique
- **WHEN** a second `Tenant` is created with an already-existing slug
- **THEN** the database raises a unique constraint violation

---

### Requirement: TenantScopedMixin applied to all domain entities
Every domain entity SHALL inherit `TenantScopedMixin`, which provides: `id` (UUID PK, auto-generated), `tenant_id` (UUID FK → Tenant, NOT NULL), `created_at` (timestamp, auto-set on insert), `updated_at` (timestamp, auto-set on update), `deleted_at` (timestamp, nullable — soft delete marker).

#### Scenario: Mixin columns are present on a domain entity
- **WHEN** a domain entity model class inherits `TenantScopedMixin`
- **THEN** it has columns `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`

---

### Requirement: BaseRepository enforces tenant scope on every query
The `BaseRepository[T]` SHALL automatically apply `WHERE tenant_id = <current_tenant> AND deleted_at IS NULL` to every read operation (`get`, `list`). A query that omits `tenant_id` filtering SHALL be impossible via this repository.

#### Scenario: Records from another tenant are never returned
- **WHEN** tenant A has a record and `BaseRepository` is initialized with tenant B's id
- **THEN** `get` and `list` return no records for tenant A's data

#### Scenario: Soft-deleted records are excluded from reads
- **WHEN** a record has `deleted_at` set to a non-null timestamp
- **THEN** `list` and `get` do not return that record

---

### Requirement: Soft delete never performs physical deletion
The system SHALL use soft delete exclusively. `BaseRepository.soft_delete` SHALL set `deleted_at = now()` on the record. No `DELETE` SQL statement SHALL be executed by the repository on domain entities.

#### Scenario: Soft-deleted record remains in database
- **WHEN** `soft_delete` is called on a record
- **THEN** the record still exists in the database with `deleted_at` set, and is not returned by `list` or `get`

---

### Requirement: Timestamps are set automatically
`created_at` SHALL be set automatically on insert. `updated_at` SHALL be set automatically on insert and on every update.

#### Scenario: created_at and updated_at set on creation
- **WHEN** a new entity is persisted via `BaseRepository.create`
- **THEN** both `created_at` and `updated_at` are non-null and approximately equal to the current UTC time

#### Scenario: updated_at changes on update
- **WHEN** an entity is updated via `BaseRepository.update`
- **THEN** `updated_at` is greater than the original value

---

### Requirement: Alembic migration 0001 creates the tenants table
The system SHALL have a migration `0001_tenant` that creates the `tenants` table. The migration SHALL be reversible (downgrade drops the table).

#### Scenario: Migration applies cleanly on empty database
- **WHEN** `alembic upgrade head` is run on an empty database
- **THEN** the `tenants` table exists with all required columns

#### Scenario: Migration is reversible
- **WHEN** `alembic downgrade -1` is run after applying `0001_tenant`
- **THEN** the `tenants` table no longer exists
