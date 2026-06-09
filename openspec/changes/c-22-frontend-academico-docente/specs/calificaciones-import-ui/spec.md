## ADDED Requirements

### Requirement: Docente puede hacer preview de calificaciones desde archivo LMS
El sistema SHALL permitir al usuario con permiso `calificaciones:importar` cargar un archivo (.xlsx o .csv) y ver un preview de las actividades detectadas antes de confirmar la importación.

#### Scenario: Upload exitoso muestra actividades detectadas
- **WHEN** el usuario carga un archivo válido (.xlsx/.csv) en el formulario de importación
- **THEN** el sistema llama a `POST /v1/calificaciones/{materia_id}/preview` y muestra las listas de actividades numéricas y textuales detectadas, con una preview de alumnos

#### Scenario: Archivo inválido muestra error
- **WHEN** el usuario carga un archivo sin columna `Email address` u otro formato no soportado
- **THEN** el sistema muestra el mensaje de error devuelto por el backend (HTTP 422) sin mostrar la lista de actividades

### Requirement: Docente selecciona actividades a importar
El sistema SHALL mostrar checkboxes para cada actividad detectada en el preview. El usuario MUST seleccionar al menos una actividad numérica antes de confirmar.

#### Scenario: Confirmación con actividades seleccionadas
- **WHEN** el usuario selecciona al menos una actividad numérica y confirma
- **THEN** el sistema llama a `POST /v1/calificaciones/{materia_id}/importar` con el archivo y las actividades seleccionadas, y muestra el conteo de calificaciones importadas

#### Scenario: Confirmación sin actividades muestra validación
- **WHEN** el usuario intenta confirmar sin seleccionar ninguna actividad
- **THEN** el sistema muestra un mensaje de validación inline y no realiza la llamada al backend

### Requirement: Docente configura umbral de aprobación
El sistema SHALL proveer un formulario para configurar `umbral_pct` (número entre 0 y 100) para la asignación del docente en la materia.

#### Scenario: Umbral válido se guarda
- **WHEN** el usuario ingresa un porcentaje válido (0-100) y confirma
- **THEN** el sistema llama a `PUT /v1/calificaciones/{materia_id}/umbral` y muestra confirmación de éxito

#### Scenario: Umbral inválido muestra error Zod
- **WHEN** el usuario ingresa un valor fuera del rango 0-100 o vacío
- **THEN** el sistema muestra el error de validación Zod inline sin llamar al backend
