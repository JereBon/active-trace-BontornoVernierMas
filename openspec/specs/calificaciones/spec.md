## ADDED Requirements

### Requirement: Modelo Calificacion con campo aprobado derivado
El sistema SHALL persistir calificaciones de alumnos con `nota_numerica` (decimal, nullable), `nota_textual` (texto, nullable), y un campo `aprobado` (booleano) calculado por el servicio antes de persistir. Al menos uno de los dos campos de nota debe estar presente. El campo `aprobado` se deriva: si `nota_numerica` existe, se compara con `UmbralMateria.umbral_pct`; si solo existe `nota_textual`, se evalúa contra la lista de valores aprobatorios configurados para la materia.

#### Scenario: Nota numérica por encima del umbral
- **WHEN** se persiste una `Calificacion` con `nota_numerica = 75` para una materia con `umbral_pct = 60`
- **THEN** `aprobado = true`

#### Scenario: Nota numérica por debajo del umbral
- **WHEN** se persiste una `Calificacion` con `nota_numerica = 45` para una materia con `umbral_pct = 60`
- **THEN** `aprobado = false`

#### Scenario: Nota textual aprobatoria
- **WHEN** se persiste una `Calificacion` con `nota_textual = "Satisfactorio"` y sin `nota_numerica`
- **THEN** `aprobado = true`

#### Scenario: Nota textual no aprobatoria
- **WHEN** se persiste una `Calificacion` con `nota_textual = "No satisfactorio"` y sin `nota_numerica`
- **THEN** `aprobado = false`

#### Scenario: Nota numérica exactamente en el umbral
- **WHEN** se persiste una `Calificacion` con `nota_numerica = 60` para una materia con `umbral_pct = 60`
- **THEN** `aprobado = true`

---

### Requirement: Importar calificaciones desde archivo LMS con preview (F1.1)
El sistema SHALL procesar un archivo `.xlsx` o `.csv` exportado del LMS en dos pasos: (1) preview sin persistir, (2) confirmar importación con selección de actividades. El preview SHALL devolver la lista de actividades detectadas y una muestra de los alumnos con sus notas. Solo las columnas con encabezado que termina en `(Real)` se detectan como actividades numéricas (RN-01). Las demás columnas no numéricas se detectan como actividades de escala textual (RN-02). El alumno se identifica por la columna `Email address` del export.

#### Scenario: Preview exitoso - detección de columnas numéricas
- **WHEN** se sube un archivo xlsx con columnas `Email address`, `Actividad A (Real)`, `Actividad B (Real)`
- **THEN** el preview devuelve `actividades_numericas = ["Actividad A", "Actividad B"]`
- **AND** no se persiste ningún dato

#### Scenario: Preview exitoso - detección de columnas textuales
- **WHEN** se sube un archivo xlsx con columnas `Email address`, `TP1`, `TP2`
- **THEN** el preview devuelve `actividades_textuales = ["TP1", "TP2"]`
- **AND** no se persiste ningún dato

#### Scenario: Confirmación de importación con selección de actividades
- **WHEN** el cliente llama al endpoint de importación con el archivo y la lista de actividades seleccionadas `["Actividad A", "TP1"]`
- **THEN** se crean registros `Calificacion` solo para las actividades seleccionadas
- **AND** cada registro tiene `aprobado` calculado correctamente
- **AND** se registra evento `CALIFICACIONES_IMPORTAR` en el audit log

#### Scenario: Archivo sin columna de identificación de alumno
- **WHEN** se sube un archivo que no contiene la columna `Email address`
- **THEN** el sistema devuelve `422` con mensaje de error indicando la columna faltante
- **AND** no se persiste ningún dato

#### Scenario: Importación re-importa actividades existentes
- **WHEN** ya existen `Calificacion` para la misma `(entrada_padron_id, actividad)`
- **AND** se importa el mismo archivo con la misma actividad
- **THEN** el registro existente se actualiza (upsert) con los nuevos valores
- **AND** no se crean registros duplicados

---

### Requirement: Configurar umbral de aprobación por materia (F2.1 / RN-03)
El sistema SHALL permitir al PROFESOR autenticado crear o actualizar el umbral de aprobación para su asignación en una materia. El umbral por defecto es 60. La operación SHALL ser un upsert: crea si no existe, actualiza si ya existe para esa `(asignacion_id, materia_id)`. Cambiar el umbral SHALL disparar el recálculo del campo `aprobado` en todas las `Calificacion` numéricas existentes de esa asignación en esa materia.

#### Scenario: Crear umbral por primera vez
- **WHEN** no existe `UmbralMateria` para `(asignacion_id=X, materia_id=Y)`
- **AND** el PROFESOR llama al endpoint con `umbral_pct = 70`
- **THEN** se crea un `UmbralMateria` con `umbral_pct = 70`
- **AND** el campo `aprobado` se recalcula para las calificaciones numéricas existentes de esa asignación

#### Scenario: Actualizar umbral existente
- **WHEN** ya existe `UmbralMateria` con `umbral_pct = 60` para `(asignacion_id=X, materia_id=Y)`
- **AND** el PROFESOR llama al endpoint con `umbral_pct = 75`
- **THEN** el `umbral_pct` se actualiza a 75
- **AND** el campo `aprobado` se recalcula en todas las calificaciones numéricas de esa asignación

#### Scenario: Umbral de un docente no afecta a otro
- **WHEN** existen dos asignaciones A y B para la misma materia (dos docentes)
- **AND** el docente A actualiza su umbral a 80
- **THEN** `UmbralMateria` del docente B no cambia
- **AND** las calificaciones del docente B no se recalculan

---

### Requirement: Tenant isolation en calificaciones
El sistema SHALL garantizar que todas las consultas de calificaciones estén scoped por `tenant_id`. Un usuario de un tenant no SHALL poder acceder a calificaciones de otro tenant.

#### Scenario: Query siempre filtra por tenant
- **WHEN** el repositorio de calificaciones recibe una consulta sin `tenant_id` explícito
- **THEN** el sistema usa el `tenant_id` de la sesión JWT
- **AND** no devuelve registros de otros tenants
