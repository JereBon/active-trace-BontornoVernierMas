## ADDED Requirements

### Requirement: Perfil completo del usuario con PII cifrada
El sistema SHALL almacenar los datos de perfil del usuario (nombre, apellidos, DNI, CUIL, CBU, alias_cbu, banco, regional, legajo, legajo_profesional, facturador) con los campos sensibles cifrados en AES-256 en reposo. Ningún campo PII SHALL exponerse en logs ni en texto plano en ninguna capa.

#### Scenario: PII cifrada en base de datos
- **WHEN** se crea o actualiza un usuario con datos PII (DNI, CUIL, CBU, alias_cbu, email)
- **THEN** el valor almacenado en la columna de la base de datos es el ciphertext AES-256, no el valor en texto plano

#### Scenario: PII descifrada en response
- **WHEN** un usuario autenticado con permiso `usuarios:gestionar` solicita el detalle de un usuario
- **THEN** la respuesta JSON contiene los valores PII en texto plano (descifrados) y nunca expone el ciphertext

### Requirement: Endpoint de gestión de usuarios (ABM)
El sistema SHALL proveer endpoints de crear, leer, actualizar y desactivar usuarios, protegidos por `require_permission("usuarios:gestionar")`.

#### Scenario: Crear usuario con permiso
- **WHEN** un usuario con permiso `usuarios:gestionar` realiza `POST /api/users` con payload válido
- **THEN** el sistema crea el usuario, cifra los campos PII, y retorna 201 con el perfil del nuevo usuario

#### Scenario: Crear usuario sin permiso
- **WHEN** un usuario sin permiso `usuarios:gestionar` realiza `POST /api/users`
- **THEN** el sistema retorna 403

#### Scenario: Listar usuarios del tenant
- **WHEN** un usuario con permiso `usuarios:gestionar` realiza `GET /api/users`
- **THEN** el sistema retorna solo los usuarios del mismo tenant, sin cruzar datos entre tenants

#### Scenario: Desactivar usuario (soft delete)
- **WHEN** un usuario con permiso `usuarios:gestionar` realiza `PUT /api/users/{id}/deactivate`
- **THEN** el usuario queda con `estado = Inactivo` y el registro se conserva en base de datos

### Requirement: Endpoint de perfil propio
El sistema SHALL proveer `GET /api/me` que retorna el perfil completo del usuario autenticado sin requerir permiso especial.

#### Scenario: Ver perfil propio
- **WHEN** cualquier usuario autenticado realiza `GET /api/me`
- **THEN** el sistema retorna el perfil del usuario derivado del JWT, con datos PII descifrados

#### Scenario: Perfil derivado del JWT
- **WHEN** el token JWT corresponde a un usuario con `id = X`
- **THEN** `GET /api/me` retorna exactamente los datos del usuario `X`, sin aceptar ningún parámetro de identidad en la URL ni en el body
