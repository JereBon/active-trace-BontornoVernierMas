## ADDED Requirements

### Requirement: Login con email y password
El sistema SHALL presentar una página de login en la ruta `/login` con campos email y password. Al enviar credenciales válidas, el sistema MUST almacenar el access token en memoria y el refresh token en `localStorage`, luego redirigir al usuario a `/dashboard`.

#### Scenario: Login exitoso
- **WHEN** el usuario envía email y password correctos
- **THEN** el sistema almacena el access token en memoria, el refresh token en localStorage, y redirige a `/dashboard`

#### Scenario: Credenciales inválidas
- **WHEN** el usuario envía credenciales incorrectas
- **THEN** el sistema muestra el mensaje de error del servidor en el formulario sin limpiar los campos

#### Scenario: Validación de campos vacíos
- **WHEN** el usuario intenta enviar el formulario con campos vacíos
- **THEN** el sistema muestra errores de validación inline sin llamar al backend

#### Scenario: Usuario ya autenticado visita /login
- **WHEN** existe un access token válido en memoria y el usuario navega a `/login`
- **THEN** el sistema redirige automáticamente a `/dashboard`

### Requirement: Refresh automático del access token
El sistema SHALL interceptar respuestas 401 del backend y, si existe un refresh token válido en localStorage, ejecutar automáticamente `POST /api/auth/refresh` para obtener un nuevo access token y reintentar la request original, sin que el usuario note la interrupción.

#### Scenario: Refresh exitoso tras 401
- **WHEN** una request recibe 401 y hay un refresh token válido en localStorage
- **THEN** el sistema llama a `/api/auth/refresh`, actualiza el access token en memoria, y reintenta la request original con el nuevo token

#### Scenario: Refresh fallido (token expirado)
- **WHEN** una request recibe 401 y el refresh también falla (401 o 403)
- **THEN** el sistema limpia el estado de sesión (token en memoria + localStorage) y redirige a `/login`

#### Scenario: Múltiples requests concurrentes con 401
- **WHEN** varias requests fallan con 401 simultáneamente
- **THEN** solo se ejecuta un refresh; las demás requests esperan en cola y se reintentan con el nuevo token obtenido

### Requirement: Logout
El sistema SHALL permitir al usuario cerrar sesión. Al hacer logout, MUST limpiar el access token en memoria y el refresh token en localStorage, y redirigir a `/login`.

#### Scenario: Logout exitoso
- **WHEN** el usuario ejecuta la acción de logout
- **THEN** el sistema limpia todos los tokens y redirige a `/login`

### Requirement: Scaffold de challenge 2FA
El sistema SHALL detectar la respuesta `{"challenge": "2fa_required", "challenge_token": "..."}` del backend en el flujo de login y mostrar un estado de challenge (pantalla o modal placeholder) para ingresar el código TOTP. La implementación completa del 2FA se hace en un change posterior; este change solo crea el scaffold.

#### Scenario: Backend responde con challenge 2FA
- **WHEN** el backend responde al login con `challenge: "2fa_required"`
- **THEN** el sistema muestra la pantalla/modal de challenge con un campo de código TOTP y almacena el `challenge_token` temporalmente
