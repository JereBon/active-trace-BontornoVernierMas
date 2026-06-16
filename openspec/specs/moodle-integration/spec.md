## ADDED Requirements

### Requirement: Cliente Moodle Web Services async
El sistema SHALL proveer un cliente async (`MoodleWSClient`) que consuma la API estándar de Moodle Web Services para obtener usuarios inscritos en cursos. El cliente recibe `moodle_url` y `token` como parámetros de construcción.

#### Scenario: Obtener usuarios inscritos exitosamente
- **WHEN** se llama a `get_enrolled_users(course_id)` con credenciales válidas
- **THEN** el cliente devuelve una lista de usuarios con nombre, apellidos y email

#### Scenario: Error de conectividad mapea a MoodleWSError
- **WHEN** Moodle no está disponible o devuelve un error HTTP 5xx
- **THEN** el cliente lanza `MoodleWSError`
- **AND** el router mapea esto a una respuesta `502 Bad Gateway`

#### Scenario: Health check antes de sync
- **WHEN** se ejecuta `health_check()`
- **AND** Moodle WS responde correctamente
- **THEN** el método devuelve `True`

#### Scenario: Health check falla
- **WHEN** se ejecuta `health_check()`
- **AND** Moodle WS no responde o devuelve error
- **THEN** el método devuelve `False`

### Requirement: Retry con backoff exponencial
El sistema SHALL reintentar las llamadas fallidas a Moodle WS hasta 3 veces con backoff exponencial (1s, 2s, 4s) solo para errores de red. Los errores HTTP 4xx no se reintentan.

#### Scenario: Reintento ante error de red
- **WHEN** la primera llamada a Moodle WS falla por timeout o error de conexión
- **THEN** el cliente reintenta hasta 3 veces con espera exponencial
- **AND** si todos los intentos fallan, lanza `MoodleWSError`

#### Scenario: No reintento ante error 4xx
- **WHEN** Moodle WS devuelve un error HTTP 4xx (ej: 401, 403)
- **THEN** el cliente lanza `MoodleWSError` inmediatamente sin reintentar

### Requirement: Sincronización on-demand desde endpoint
El sistema SHALL exponer un endpoint `POST /padron/sync-moodle/{materia_id}` para sincronizar el padrón de una materia desde Moodle WS on-demand. Requiere permiso `padron:cargar`.

#### Scenario: Sync on-demand exitoso
- **WHEN** un usuario con permiso `padron:cargar` llama al endpoint de sync
- **AND** Moodle WS responde correctamente
- **THEN** se importa el padrón como nueva `VersionPadron`
- **AND** se registra evento `PADRON_CARGAR` en audit log

#### Scenario: Sync on-demand con Moodle caído
- **WHEN** un usuario con permiso `padron:cargar` llama al endpoint de sync
- **AND** Moodle WS no está disponible
- **THEN** el endpoint devuelve `502`
- **AND** el padrón existente no se modifica

### Requirement: Aislamiento de tenant en configuración Moodle
El sistema SHALL almacenar la URL y token de Moodle WS cifrados (AES-256) en la configuración del tenant. No se exponen en texto plano en logs ni en respuestas de API.

#### Scenario: Token no aparece en respuestas
- **WHEN** se consulta la configuración de integración Moodle de un tenant
- **THEN** el token de Moodle WS NO aparece en la respuesta de la API
- **AND** solo se expone un indicador booleano de si la integración está configurada
