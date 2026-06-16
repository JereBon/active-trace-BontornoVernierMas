## ADDED Requirements

### Requirement: Docente ve tabla de alumnos atrasados
El sistema SHALL mostrar una tabla con todos los alumnos atrasados de la materia, incluyendo nombre, comisión y actividades faltantes/reprobadas. La tabla SHALL soportar paginación client-side.

#### Scenario: Tabla muestra atrasados correctamente
- **WHEN** el usuario navega a la vista de atrasados de una materia
- **THEN** el sistema llama a `GET /v1/analisis/atrasados?materia_id=` y muestra la tabla con nombre, apellidos, comisión y actividades pendientes de cada alumno

#### Scenario: Sin atrasados muestra estado vacío
- **WHEN** el endpoint devuelve lista vacía
- **THEN** el sistema muestra un mensaje de estado vacío (sin tabla)

### Requirement: Docente ve ranking de aprobados
El sistema SHALL mostrar un ranking de alumnos ordenado por cantidad de actividades aprobadas.

#### Scenario: Ranking se muestra correctamente
- **WHEN** el usuario navega a la sección ranking
- **THEN** el sistema llama a `GET /v1/analisis/ranking?materia_id=` y muestra la tabla ordenada por aprobados descendente

### Requirement: Docente ve notas finales
El sistema SHALL mostrar la nota final calculada por alumno.

#### Scenario: Notas finales se muestran
- **WHEN** el usuario navega a la sección notas finales
- **THEN** el sistema llama a `GET /v1/analisis/notas-finales?materia_id=` y muestra nombre, apellidos y nota promedio de cada alumno

### Requirement: Docente ve reporte agregado de la materia
El sistema SHALL mostrar métricas agregadas de la materia (totales, porcentajes de aprobación).

#### Scenario: Reporte se muestra correctamente
- **WHEN** el usuario navega a la sección reporte
- **THEN** el sistema llama a `GET /v1/analisis/reporte-materia?materia_id=` y muestra las métricas en cards/badges
