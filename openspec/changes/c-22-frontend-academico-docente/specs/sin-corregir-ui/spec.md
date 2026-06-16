## ADDED Requirements

### Requirement: Docente ve entregas textuales sin corregir
El sistema SHALL mostrar un listado de actividades textuales finalizadas por el alumno en el LMS pero sin nota asignada aún.

#### Scenario: Listado de sin corregir se muestra correctamente
- **WHEN** el usuario navega a la sección entregas sin corregir
- **THEN** el sistema llama a `GET /v1/analisis/sin-corregir?materia_id=` y muestra nombre, apellidos, actividad y fecha de importación

#### Scenario: Sin pendientes muestra estado vacío
- **WHEN** el endpoint devuelve lista vacía
- **THEN** el sistema muestra un mensaje indicando que no hay entregas pendientes de corrección

### Requirement: Docente puede exportar listado de sin corregir en CSV
El sistema SHALL proveer un botón de export que descargue los datos de entregas sin corregir como archivo CSV, sin llamar a ningún endpoint adicional.

#### Scenario: Export CSV descarga archivo
- **WHEN** el usuario hace clic en el botón "Exportar CSV" con datos cargados
- **THEN** el sistema genera un CSV en memoria con los datos de la tabla y lo descarga como archivo `sin-corregir-{fecha}.csv`

#### Scenario: Export deshabilitado sin datos
- **WHEN** la lista de sin corregir está vacía o cargando
- **THEN** el botón de exportar CSV está deshabilitado
