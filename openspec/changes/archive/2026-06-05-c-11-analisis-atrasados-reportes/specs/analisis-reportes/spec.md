## ADDED Requirements

### Requirement: Reporte rápido de estado por materia (F2.4)
El sistema SHALL devolver métricas consolidadas de una materia a partir de los datos importados: total de alumnos en padrón activo, total de actividades en el conjunto, cantidad de alumnos con al menos una aprobada, cantidad de alumnos atrasados, porcentaje de aprobación global. Si no hay datos importados, el sistema SHALL devolver ceros en todos los campos numéricos, no un error. El endpoint SHALL requerir permiso `atrasados:ver`.

#### Scenario: Reporte con datos
- **WHEN** existe un padrón activo con 10 alumnos y calificaciones importadas
- **THEN** el reporte devuelve `total_alumnos = 10`, `total_actividades >= 1`, porcentajes calculados

#### Scenario: Reporte sin datos importados
- **WHEN** existe un padrón activo pero no hay calificaciones importadas para la materia
- **THEN** el reporte devuelve todos los campos numéricos en cero sin error

#### Scenario: Guard de permiso aplicado
- **WHEN** un usuario sin permiso `atrasados:ver` llama al endpoint de reporte
- **THEN** el sistema responde `403 Forbidden`

---

### Requirement: Exportar trabajos prácticos sin corregir (F2.6 / RN-07 / RN-08)
El sistema SHALL detectar y devolver las entregas que tienen `finalizado_lms = true` en la tabla `Calificacion` pero cuyo `nota_textual` es `null` (entregado pero sin calificación). Solo se incluyen actividades de escala textual (RN-08): aquellas donde `nota_numerica` es `null`. La respuesta es una lista descargable (JSON o CSV según `Accept` header) con: nombre del alumno, apellidos, comisión, nombre de actividad, fecha de finalización (`importado_at`). El endpoint SHALL requerir permiso `atrasados:ver`.

#### Scenario: Entrega sin corregir detectada
- **WHEN** una `Calificacion` tiene `finalizado_lms = true`, `nota_textual = null` y `nota_numerica = null`
- **THEN** esa entrega aparece en la lista de "sin corregir"

#### Scenario: Actividades numéricas excluidas
- **WHEN** una `Calificacion` tiene `finalizado_lms = true`, `nota_textual = null` pero `nota_numerica IS NOT NULL`
- **THEN** esa entrega NO aparece en la lista (RN-08: solo escala textual)

#### Scenario: Entrega ya calificada excluida
- **WHEN** una `Calificacion` tiene `finalizado_lms = true` y `nota_textual = "Satisfactorio"`
- **THEN** esa entrega NO aparece en la lista (ya está corregida)

#### Scenario: Lista vacía cuando todo está corregido
- **WHEN** todas las entregas tienen `nota_textual` no nulo
- **THEN** la respuesta devuelve una lista vacía sin error

---

### Requirement: Migration 0012 — campo finalizado_lms en Calificacion
El sistema SHALL agregar el campo `finalizado_lms` (booleano, no nulo, default `false`) al modelo `Calificacion` para soportar la detección de TPs sin corregir (RN-07). Este campo se persiste `true` cuando el LMS reporta que el alumno finalizó la actividad (reporte de finalización importado por F1.2).

#### Scenario: Default false en registros existentes
- **WHEN** se aplica la migration 0012
- **THEN** todos los registros `Calificacion` existentes tienen `finalizado_lms = false`

#### Scenario: Importación de reporte de finalización setea el campo
- **WHEN** se importa el reporte de finalización del LMS para una actividad de un alumno
- **THEN** la `Calificacion` correspondiente tiene `finalizado_lms = true`
