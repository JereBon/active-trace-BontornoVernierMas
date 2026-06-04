## MODIFIED Requirements

### Requirement: Modelo de usuario con perfil extendido
El sistema SHALL mantener el modelo `Usuario` con todos los campos de autenticación existentes (email_cifrado, email_hash, password_hash, totp_secret, totp_activo, estado, ultimo_acceso) MÁS los campos de perfil PII (nombre, apellidos, dni_cifrado, cuil_cifrado, cbu_cifrado, alias_cbu_cifrado, banco, regional, legajo, legajo_profesional, facturador). Los campos PII son nullable para compatibilidad con usuarios ya existentes.

#### Scenario: Usuario existente de auth sigue funcionando
- **WHEN** existe un usuario creado antes de este change (solo con campos de auth)
- **THEN** el usuario puede autenticarse y usar `GET /api/me` sin error, con los campos PII retornando `null`

#### Scenario: Usuario con perfil completo
- **WHEN** se crea un usuario con todos los campos incluyendo PII
- **THEN** la autenticación y el perfil funcionan correctamente con todos los datos disponibles
