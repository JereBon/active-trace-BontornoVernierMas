## ADDED Requirements

### Requirement: Usuario ve monitor de seguimiento de alumnos
El sistema SHALL mostrar una tabla de seguimiento con estado de actividades por alumno. Los filtros opcionales (materia, comisión, regional, nombre, solo atrasados) se aplican via query params al endpoint.

#### Scenario: Monitor carga con datos
- **WHEN** el usuario navega a la sección monitor
- **THEN** el sistema llama a `GET /v1/analisis/monitor` con los filtros activos y muestra la tabla con nombre, comisión, materia y estado de actividades

#### Scenario: Filtro de solo atrasados reduce la tabla
- **WHEN** el usuario activa el toggle "Solo atrasados"
- **THEN** el sistema re-llama al endpoint con `solo_atrasados=true` y actualiza la tabla mostrando únicamente alumnos atrasados

#### Scenario: Monitor vacío muestra estado vacío
- **WHEN** el endpoint devuelve lista vacía con los filtros activos
- **THEN** el sistema muestra un mensaje de estado vacío (sin tabla)

### Requirement: Monitor soporta paginación
El sistema SHALL paginar la tabla del monitor con parámetros `limit` y `offset` enviados al endpoint.

#### Scenario: Navegación de páginas actualiza datos
- **WHEN** el usuario hace clic en siguiente/anterior página
- **THEN** el sistema llama al endpoint con los nuevos valores de `offset` y `limit` y actualiza la tabla
