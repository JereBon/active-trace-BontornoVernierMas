## ADDED Requirements

### Requirement: Detectar alumnos atrasados por materia (F2.2 / RN-06)
El sistema SHALL calcular la lista de alumnos atrasados de una materia para la versión de padrón activa. Un alumno es atrasado si cumple al menos una de las dos condiciones: (a) tiene actividades faltantes — alguna actividad del conjunto de la materia no tiene `Calificacion` para ese alumno; (b) alguna de sus `Calificacion` tiene `aprobado = false`. El endpoint SHALL requerir permiso `atrasados:ver`. La identidad del tenant proviene exclusivamente del JWT. La respuesta incluye para cada alumno atrasado: nombre, apellidos, comisión, lista de actividades faltantes y lista de actividades no aprobadas.

#### Scenario: Alumno sin ninguna calificación
- **WHEN** un alumno en el padrón activo no tiene ninguna `Calificacion` para la materia
- **THEN** el alumno aparece en la lista de atrasados con todas las actividades del conjunto como "faltantes"

#### Scenario: Alumno con nota por debajo del umbral
- **WHEN** un alumno tiene `Calificacion` con `aprobado = false` para alguna actividad
- **THEN** el alumno aparece en la lista de atrasados con esa actividad en "no aprobadas"

#### Scenario: Alumno con todas las actividades aprobadas
- **WHEN** un alumno tiene `aprobado = true` para todas las actividades del conjunto de la materia
- **THEN** el alumno NO aparece en la lista de atrasados

#### Scenario: Conjunto de actividades es la unión de actividades del tenant
- **WHEN** se calculan los atrasados de una materia
- **THEN** el conjunto de actividades esperadas es la unión de todos los nombres de actividad distintos en `Calificacion` para esa materia y tenant

#### Scenario: Guard de permiso aplicado
- **WHEN** un usuario sin permiso `atrasados:ver` llama al endpoint
- **THEN** el sistema responde `403 Forbidden`

---

### Requirement: Ranking de actividades aprobadas por alumno (F2.3 / RN-09)
El sistema SHALL devolver una tabla ordenada descendentemente por cantidad de actividades con `aprobado = true` por alumno, incluyendo solo alumnos con al menos una actividad aprobada. Alumnos sin ninguna actividad aprobada NO aparecen en el ranking (RN-09). El endpoint SHALL requerir permiso `atrasados:ver`.

#### Scenario: Solo alumnos con al menos una aprobada
- **WHEN** existen 3 alumnos: A con 5 aprobadas, B con 0 aprobadas, C con 3 aprobadas
- **THEN** el ranking contiene solo A y C, ordenados A primero

#### Scenario: Alumno sin ninguna aprobada excluido
- **WHEN** un alumno tiene `Calificacion` pero todas con `aprobado = false`
- **THEN** ese alumno NO aparece en el ranking

#### Scenario: Empate en número de aprobadas
- **WHEN** dos alumnos tienen el mismo número de actividades aprobadas
- **THEN** se ordenan alfabéticamente por apellidos como criterio de desempate

---

### Requirement: Notas finales agrupadas por alumno (F2.5)
El sistema SHALL calcular una nota final por alumno: promedio simple de todas sus `nota_numerica` no nulas. Alumnos sin ninguna nota numérica reciben `nota_final = null`. La respuesta incluye nombre, apellidos, comisión y nota final. El endpoint SHALL requerir permiso `atrasados:ver`.

#### Scenario: Promedio simple de notas numéricas
- **WHEN** un alumno tiene calificaciones con `nota_numerica = [80, 60, 70]`
- **THEN** su `nota_final = 70.0`

#### Scenario: Alumno sin notas numéricas
- **WHEN** un alumno solo tiene calificaciones con `nota_textual` y `nota_numerica = null`
- **THEN** su `nota_final = null`

#### Scenario: Respuesta ordenada por apellidos
- **WHEN** se solicita el endpoint de notas finales
- **THEN** la lista está ordenada por apellidos ascendente

---

### Requirement: Monitor de seguimiento de alumnos (F2.7 / F2.8 / F2.9)
El sistema SHALL proveer un endpoint de monitor que devuelva el estado de actividades de todos los alumnos del tenant (para COORDINADOR/ADMIN) o solo los alumnos de las materias asignadas al usuario (para TUTOR/PROFESOR). El endpoint SHALL aceptar filtros opcionales: `materia_id`, `comision`, `regional`, `alumno_nombre` (texto libre), `solo_atrasados` (bool), `fecha_desde` y `fecha_hasta` (aplican al campo `importado_at` de `Calificacion`). Los filtros de rango de fechas son exclusivos del rol COORDINADOR/ADMIN (F2.9). El endpoint SHALL requerir permiso `atrasados:ver`.

#### Scenario: COORDINADOR ve todos los alumnos del tenant
- **WHEN** un usuario con rol COORDINADOR llama al monitor sin filtros
- **THEN** recibe alumnos de todas las materias del tenant

#### Scenario: PROFESOR solo ve alumnos de sus materias asignadas
- **WHEN** un usuario con rol PROFESOR llama al monitor sin filtros
- **THEN** recibe solo alumnos de las materias en que tiene asignaciones vigentes

#### Scenario: Filtro por materia
- **WHEN** se llama al monitor con `materia_id=X`
- **THEN** solo aparecen alumnos de esa materia

#### Scenario: Filtro solo_atrasados
- **WHEN** se llama al monitor con `solo_atrasados=true`
- **THEN** solo aparecen alumnos que tienen al menos una actividad faltante o no aprobada

#### Scenario: Filtro de rango de fechas aplica a importado_at
- **WHEN** se llama al monitor con `fecha_desde=2026-01-01` y `fecha_hasta=2026-03-31`
- **THEN** solo se incluyen calificaciones con `importado_at` dentro de ese rango
