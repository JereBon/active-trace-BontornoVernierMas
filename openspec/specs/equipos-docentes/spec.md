# equipos-docentes Specification

## Purpose
TBD - created by archiving change c-08-equipos-docentes. Update Purpose after archive.
## Requirements
### Requirement: Vista de mis asignaciones (docente autenticado)
El sistema SHALL exponer un endpoint que permita a cualquier usuario autenticado consultar sus propias asignaciones vigentes, sin requerir permiso elevado. La identidad del usuario SHALL derivarse exclusivamente de la sesión JWT.

#### Scenario: Docente consulta sus asignaciones vigentes
- **WHEN** un usuario autenticado hace `GET /v1/equipos/mis-asignaciones`
- **THEN** el sistema retorna la lista de asignaciones vigentes del usuario autenticado, filtradas por `tenant_id` de la sesión, con status 200

#### Scenario: Docente sin asignaciones recibe lista vacía
- **WHEN** un usuario autenticado hace `GET /v1/equipos/mis-asignaciones` y no tiene asignaciones vigentes
- **THEN** el sistema retorna `[]` con status 200

#### Scenario: tenant_id no puede venir de la request
- **WHEN** un usuario autenticado intenta consultar asignaciones de otro tenant (manipulando parámetros)
- **THEN** el sistema solo retorna asignaciones del tenant del JWT y nunca de otro tenant

### Requirement: Listado global de asignaciones con filtros (coordinador/admin)
El sistema SHALL exponer un endpoint de listado de todas las asignaciones del tenant, protegido con el permiso `equipos:asignar`, con filtros opcionales por materia, carrera, cohorte, usuario, rol y estado de vigencia.

#### Scenario: Coordinador lista todas las asignaciones activas
- **WHEN** un usuario con permiso `equipos:asignar` hace `GET /v1/equipos/` con `solo_vigentes=true`
- **THEN** el sistema retorna solo asignaciones donde `hasta IS NULL OR hasta >= hoy`, del tenant de la sesión, con status 200

#### Scenario: Filtro por materia acota el resultado
- **WHEN** un coordinador hace `GET /v1/equipos/?materia_id=<uuid>`
- **THEN** el sistema retorna solo asignaciones donde `materia_id` coincide con el parámetro y `tenant_id` es el del tenant de la sesión

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario sin permiso `equipos:asignar` hace `GET /v1/equipos/`
- **THEN** el sistema responde con HTTP 403

### Requirement: Alta individual de asignación
El sistema SHALL permitir crear una asignación individual con validación de rol, contexto académico y vigencia.

#### Scenario: Creación exitosa con contexto completo
- **WHEN** un usuario con permiso `equipos:asignar` hace `POST /v1/equipos/` con `usuario_id`, `rol`, `materia_id`, `carrera_id`, `cohorte_id`, `desde`
- **THEN** el sistema persiste la asignación con el `tenant_id` de la sesión y retorna el recurso creado con status 201

#### Scenario: Rol inválido es rechazado
- **WHEN** se hace `POST /v1/equipos/` con un `rol` que no pertenece al conjunto válido del dominio
- **THEN** el sistema responde con HTTP 422

#### Scenario: Auditoría registrada en creación
- **WHEN** se crea una asignación exitosamente
- **THEN** el sistema genera un registro de auditoría con acción `ASIGNACION_CREAR` y el `actor_id` del usuario autenticado

### Requirement: Edición de asignación individual
El sistema SHALL permitir actualizar los campos `rol`, `materia_id`, `carrera_id`, `cohorte_id`, `comisiones`, `responsable_id`, `desde`, `hasta` de una asignación existente.

#### Scenario: Actualización de vigencia exitosa
- **WHEN** un usuario con permiso `equipos:asignar` hace `PUT /v1/equipos/{id}` con nuevas fechas `desde`/`hasta`
- **THEN** el sistema actualiza la asignación y retorna el recurso actualizado con status 200

#### Scenario: Asignación de otro tenant no puede editarse
- **WHEN** un usuario intenta editar una asignación que pertenece a un tenant diferente al de la sesión
- **THEN** el sistema responde con HTTP 404 (no expone la existencia del registro)

#### Scenario: Auditoría registrada en edición
- **WHEN** se actualiza una asignación exitosamente
- **THEN** el sistema genera un registro de auditoría con acción `ASIGNACION_MODIFICAR`

### Requirement: Soft delete de asignación
El sistema SHALL implementar eliminación lógica de asignaciones: setea `deleted_at` y nunca elimina el registro de la base de datos.

#### Scenario: Soft delete exitoso
- **WHEN** un usuario con permiso `equipos:asignar` hace `DELETE /v1/equipos/{id}`
- **THEN** el sistema setea `deleted_at` en la asignación, retorna status 204 y la asignación deja de aparecer en listados

#### Scenario: Auditoría registrada en eliminación
- **WHEN** se elimina (soft) una asignación
- **THEN** el sistema genera un registro de auditoría con acción `ASIGNACION_ELIMINAR`

### Requirement: Asignación masiva de docentes (F4.4, RN-30)
El sistema SHALL permitir asignar múltiples docentes en bloque a una combinación materia × carrera × cohorte × rol con una vigencia definida. La operación SHALL ser idempotente: si una asignación idéntica ya existe, se omite sin abortar la operación.

#### Scenario: Asignación masiva exitosa
- **WHEN** un usuario con permiso `equipos:asignar` hace `POST /v1/equipos/asignacion-masiva` con `usuario_ids=[u1, u2, u3]`, `materia_id`, `carrera_id`, `cohorte_id`, `rol`, `desde`, `hasta`
- **THEN** el sistema crea una asignación por cada `usuario_id` y retorna la lista de asignaciones creadas con status 201

#### Scenario: Duplicado en asignación masiva es omitido
- **WHEN** algún `usuario_id` de la lista ya tiene una asignación idéntica activa para el mismo contexto y rol
- **THEN** el sistema omite ese usuario sin crear duplicado y sin abortar; la respuesta incluye los IDs omitidos en un campo `omitidos`

#### Scenario: Lista vacía de usuario_ids es rechazada
- **WHEN** se hace `POST /v1/equipos/asignacion-masiva` con `usuario_ids=[]`
- **THEN** el sistema responde con HTTP 422

### Requirement: Clonado de equipo entre cohortes (F4.5, RN-12)
El sistema SHALL permitir duplicar todas las asignaciones vigentes de un equipo origen (materia × carrera × cohorte) hacia un equipo destino (misma materia × carrera × nueva cohorte), con nuevas fechas de vigencia.

#### Scenario: Clonado exitoso entre cohortes
- **WHEN** un usuario con permiso `equipos:asignar` hace `POST /v1/equipos/clonar` con `origen_cohorte_id`, `destino_cohorte_id`, `materia_id`, `carrera_id`, `desde`, `hasta`
- **THEN** el sistema duplica todas las asignaciones vigentes del origen hacia el destino con las nuevas fechas y retorna las asignaciones creadas con status 201

#### Scenario: Asignaciones ya existentes en destino son omitidas
- **WHEN** el destino ya tiene asignaciones para alguno de los usuarios del origen
- **THEN** el sistema omite esas asignaciones sin abortar y las lista en `omitidos` en la respuesta

#### Scenario: Origen sin asignaciones vigentes retorna lista vacía
- **WHEN** el equipo origen no tiene asignaciones vigentes a clonar
- **THEN** el sistema retorna `{"creadas": [], "omitidos": []}` con status 200

### Requirement: Modificación masiva de vigencia del equipo (F4.6)
El sistema SHALL permitir actualizar las fechas `desde` y `hasta` de todas las asignaciones activas de un equipo (materia × carrera × cohorte) en una sola operación atómica.

#### Scenario: Modificación masiva de vigencia exitosa
- **WHEN** un usuario con permiso `equipos:asignar` hace `PUT /v1/equipos/vigencia-masiva` con `materia_id`, `carrera_id`, `cohorte_id`, `desde`, `hasta`
- **THEN** el sistema actualiza `desde` y `hasta` en todas las asignaciones no eliminadas del equipo y retorna la cantidad de filas afectadas con status 200

#### Scenario: Auditoría de modificación masiva
- **WHEN** se ejecuta la modificación masiva de vigencia
- **THEN** el sistema genera un registro de auditoría con acción `ASIGNACION_MODIFICAR` y `filas_afectadas` igual al número de asignaciones actualizadas

### Requirement: Exportación del equipo docente a CSV (F4.7)
El sistema SHALL generar un archivo CSV descargable con el detalle de todas las asignaciones del equipo (docente, rol, materia, carrera, cohorte, vigencia, estado).

#### Scenario: Exportación exitosa
- **WHEN** un usuario con permiso `equipos:asignar` hace `GET /v1/equipos/exportar` con los filtros del equipo deseado
- **THEN** el sistema responde con `Content-Type: text/csv`, `Content-Disposition: attachment; filename="equipo.csv"` y el contenido del CSV con los datos del equipo, con status 200

#### Scenario: Exportación con equipo vacío genera CSV con solo cabeceras
- **WHEN** no hay asignaciones que coincidan con los filtros
- **THEN** el sistema retorna un CSV con solo la fila de cabeceras y sin filas de datos

