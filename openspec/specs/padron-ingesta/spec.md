## ADDED Requirements

### Requirement: Padrón versionado por materia×cohorte
El sistema SHALL mantener versiones inmutables del padrón de alumnos. Cada carga genera una nueva `VersionPadron`. Solo puede haber una versión activa por `(tenant_id, materia_id, cohorte_id)` en simultáneo. Al activar una nueva versión, la versión anteriormente activa se desactiva (flag `activa = false`) en la misma transacción. Las versiones desactivadas se conservan para auditoría.

#### Scenario: Activar nueva versión desactiva la anterior
- **WHEN** existe una `VersionPadron` con `activa = true` para `(materia_id=X, cohorte_id=Y)`
- **AND** se confirma la carga de un nuevo padrón para ese mismo contexto
- **THEN** la versión anterior queda con `activa = false`
- **AND** la nueva versión queda con `activa = true`
- **AND** ambas versiones existen en la base de datos (no se borran)

#### Scenario: Primera carga de padrón
- **WHEN** no existe ninguna `VersionPadron` para `(materia_id=X, cohorte_id=Y)`
- **AND** se confirma la carga de un nuevo padrón
- **THEN** se crea una `VersionPadron` con `activa = true`
- **AND** se crean las `EntradaPadron` correspondientes

### Requirement: Importación desde archivo xlsx/csv con preview
El sistema SHALL aceptar archivos `.xlsx` y `.csv` para importar el padrón. El flujo es de dos pasos: (1) parsear y devolver preview, (2) confirmar para persistir. Las columnas requeridas son: `nombre`, `apellidos`, `email`, `comision`, `regional`.

#### Scenario: Preview exitoso desde xlsx
- **WHEN** se sube un archivo `.xlsx` válido con las columnas requeridas
- **THEN** el sistema devuelve una lista de `EntradaPadronPreview` (nombre, apellidos, email, comision, regional)
- **AND** no se persiste ningún dato aún

#### Scenario: Preview exitoso desde csv
- **WHEN** se sube un archivo `.csv` válido con las columnas requeridas
- **THEN** el sistema devuelve una lista de `EntradaPadronPreview`
- **AND** no se persiste ningún dato aún

#### Scenario: Archivo con columnas faltantes
- **WHEN** se sube un archivo que no contiene todas las columnas requeridas
- **THEN** el sistema devuelve `422` con la lista de columnas faltantes
- **AND** no se persiste ningún dato

#### Scenario: Confirmación de importación
- **WHEN** el cliente llama al endpoint de confirmación con un preview token válido
- **THEN** se crea una nueva `VersionPadron` con las entradas parseadas
- **AND** la versión anterior (si existe) queda desactivada
- **AND** se registra evento `PADRON_CARGAR` en audit log

### Requirement: EntradaPadron sin usuario_id
El sistema SHALL permitir crear `EntradaPadron` con `usuario_id = NULL` para alumnos que aún no tienen cuenta en el sistema.

#### Scenario: Entrada sin cuenta de usuario
- **WHEN** se importa un padrón que incluye un alumno cuyo email no corresponde a ningún `Usuario` existente
- **THEN** se crea la `EntradaPadron` con `usuario_id = NULL`
- **AND** los campos `nombre`, `apellidos`, `email`, `comision`, `regional` quedan registrados

#### Scenario: Tenant isolation en entradas
- **WHEN** se consultan las `EntradaPadron` de una versión
- **THEN** solo se devuelven entradas cuyo `tenant_id` coincide con el tenant del JWT
- **AND** no se exponen entradas de otros tenants

### Requirement: Vaciado scope-isolated de padrón (RN-04)
El sistema SHALL permitir vaciar todas las versiones de padrón para una materia. El vaciado aplica soft delete y es scope-isolated: solo afecta los datos del usuario que ejecuta la operación en esa materia. No elimina datos de otros docentes ni de otros tenants.

#### Scenario: Vaciado exitoso
- **WHEN** un PROFESOR o COORDINADOR llama a `DELETE /padron/materia/{materia_id}` con permiso `padron:vaciar`
- **THEN** todas las `VersionPadron` + `EntradaPadron` del tenant para esa materia quedan con `deleted_at` no nulo
- **AND** se registra evento `PADRON_CARGAR` con acción `VACIAR` en audit log

#### Scenario: Vaciado no afecta otros tenants
- **WHEN** se vacía el padrón de `materia_id=X` en `tenant_id=T1`
- **THEN** las `VersionPadron` de `materia_id=X` en `tenant_id=T2` no se modifican

### Requirement: Control de acceso RBAC para padrón
El sistema SHALL requerir permiso `padron:cargar` para importar y `padron:vaciar` para vaciar. El permiso `padron:leer` se requiere para consultar versiones y entradas. La identidad se obtiene SIEMPRE del JWT; nunca de parámetros de la petición.

#### Scenario: Carga sin permiso
- **WHEN** un usuario sin permiso `padron:cargar` intenta subir un archivo de padrón
- **THEN** el sistema devuelve `403`

#### Scenario: Vaciado sin permiso
- **WHEN** un usuario sin permiso `padron:vaciar` intenta vaciar el padrón
- **THEN** el sistema devuelve `403`
