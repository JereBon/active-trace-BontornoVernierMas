# frontend-coordinacion Specification

## Purpose
TBD - created by archiving change c-23-frontend-coordinacion. Update Purpose after archive.
## Requirements
### Requirement: Gestión de equipos docentes
El sistema SHALL permitir al COORDINADOR/ADMIN crear, editar, dar de baja, clonar y exportar equipos docentes mediante una interfaz web.

#### Scenario: Listar equipos
- **WHEN** el COORDINADOR navega a `/coordinacion/equipos`
- **THEN** se muestra la tabla de equipos docentes del tenant con columnas: nombre, vigencia, integrantes, acciones

#### Scenario: Crear equipo
- **WHEN** el COORDINADOR completa el formulario y confirma
- **THEN** se envía `POST /v1/equipos-docentes` y el nuevo equipo aparece en la tabla

#### Scenario: Editar equipo
- **WHEN** el COORDINADOR hace clic en "Editar" de un equipo
- **THEN** se abre el formulario con datos pre-cargados y al confirmar se envía `PUT /v1/equipos-docentes/{id}`

#### Scenario: Dar de baja equipo
- **WHEN** el COORDINADOR confirma la baja de un equipo
- **THEN** se envía `DELETE /v1/equipos-docentes/{id}` y el equipo desaparece de la tabla activa

#### Scenario: Clonar equipo de cuatrimestre anterior
- **WHEN** el COORDINADOR hace clic en "Clonar" y selecciona un cuatrimestre origen
- **THEN** se envía `POST /v1/equipos-docentes/clonar` con el id origen y aparece el nuevo equipo

#### Scenario: Exportar CSV
- **WHEN** el COORDINADOR hace clic en "Exportar CSV"
- **THEN** el navegador descarga un archivo `.csv` con los datos de todos los equipos visibles

### Requirement: Gestión de avisos
El sistema SHALL permitir al COORDINADOR/ADMIN publicar, editar y archivar avisos con scope, severidad, vigencia y requerimiento de acknowledgment.

#### Scenario: Listar avisos
- **WHEN** el COORDINADOR navega a `/coordinacion/avisos`
- **THEN** se muestra la tabla de avisos con columnas: título, scope, severidad, vigencia, ack requerido, estado

#### Scenario: Publicar aviso
- **WHEN** el COORDINADOR completa el formulario de aviso y confirma
- **THEN** se envía `POST /v1/avisos` con `{ titulo, cuerpo, scope, severidad, vigencia_hasta, requiere_ack }` y el aviso aparece en la lista

#### Scenario: Editar aviso activo
- **WHEN** el COORDINADOR edita un aviso en estado activo y confirma
- **THEN** se envía `PUT /v1/avisos/{id}` con los campos actualizados

#### Scenario: Archivar aviso
- **WHEN** el COORDINADOR hace clic en "Archivar" de un aviso
- **THEN** se envía `PATCH /v1/avisos/{id}` con `{ activo: false }` y el aviso pasa a estado archivado

### Requirement: Gestión de tareas internas
El sistema SHALL permitir al COORDINADOR/ADMIN crear tareas, asignarlas, cambiar su estado, delegarlas y ver el hilo de comentarios.

#### Scenario: Listar mis tareas asignadas
- **WHEN** el COORDINADOR navega a `/coordinacion/tareas`
- **THEN** se muestra la lista de tareas asignadas o creadas por él, con columnas: título, estado, asignado a, prioridad, vence

#### Scenario: Crear y asignar tarea
- **WHEN** el COORDINADOR completa el formulario de tarea con título, descripción, asignado, prioridad y fecha de vencimiento y confirma
- **THEN** se envía `POST /v1/tareas` y la tarea aparece en la lista

#### Scenario: Cambiar estado de tarea
- **WHEN** el COORDINADOR selecciona un nuevo estado en la tarea (Pendiente → En Progreso → Completada)
- **THEN** se envía `PATCH /v1/tareas/{id}` con `{ estado: <nuevo_estado> }` y la tarea refleja el cambio

#### Scenario: Agregar comentario
- **WHEN** el COORDINADOR escribe un comentario en el hilo de una tarea y envía
- **THEN** se envía `POST /v1/tareas/{id}/comentarios` y el comentario aparece en el hilo

#### Scenario: Filtrar tareas por estado y asignado
- **WHEN** el COORDINADOR aplica filtros de estado o asignado
- **THEN** la lista se filtra mostrando solo las tareas que cumplen los criterios

### Requirement: Monitor global de comisiones
El sistema SHALL mostrar al COORDINADOR/ADMIN una vista global del estado de todas las comisiones del tenant.

#### Scenario: Ver monitor global
- **WHEN** el COORDINADOR navega a `/coordinacion/monitor`
- **THEN** se carga `GET /v1/analisis/monitor` sin filtro de materia y se muestra la tabla con todas las comisiones

#### Scenario: Filtrar por materia o cohorte
- **WHEN** el COORDINADOR aplica filtros en el monitor global
- **THEN** la tabla se actualiza mostrando solo las comisiones que coinciden con los filtros

### Requirement: Gestión de encuentros admin
El sistema SHALL permitir al COORDINADOR/ADMIN gestionar slots e instancias de encuentros.

#### Scenario: Listar encuentros
- **WHEN** el COORDINADOR navega a `/coordinacion/encuentros`
- **THEN** se muestra la lista de instancias de encuentros con fecha, tipo, cupo y estado

#### Scenario: Crear encuentro
- **WHEN** el COORDINADOR completa el formulario y confirma
- **THEN** se envía `POST /v1/encuentros` y el encuentro aparece en la lista

### Requirement: Gestión de coloquios
El sistema SHALL permitir al COORDINADOR/ADMIN gestionar convocatorias y turnos de coloquios.

#### Scenario: Listar coloquios
- **WHEN** el COORDINADOR navega a `/coordinacion/coloquios`
- **THEN** se muestra la lista de convocatorias con materia, fecha y estado

#### Scenario: Crear convocatoria
- **WHEN** el COORDINADOR completa el formulario y confirma
- **THEN** se envía `POST /v1/coloquios` y la convocatoria aparece en la lista

### Requirement: Asistente de setup de cuatrimestre
El sistema SHALL guiar al COORDINADOR a través de un asistente de 3 pasos para configurar un nuevo cuatrimestre.

#### Scenario: Completar paso 1 (materias y cohortes)
- **WHEN** el COORDINADOR selecciona materias y cohortes para el nuevo cuatrimestre y hace clic en "Siguiente"
- **THEN** el stepper avanza al paso 2 con los datos del paso 1 conservados

#### Scenario: Completar paso 2 (equipos base)
- **WHEN** el COORDINADOR asigna equipos docentes a cada materia y hace clic en "Siguiente"
- **THEN** el stepper avanza al paso 3 con el resumen de configuración

#### Scenario: Confirmar configuración
- **WHEN** el COORDINADOR revisa el resumen y hace clic en "Confirmar"
- **THEN** se envían los requests de creación necesarios y se redirige a la vista principal de coordinación

