# Guía de Prueba — Coordinación en Navegador

> Asumiendo que el backend y frontend corren en Docker (`docker compose up`).
> Frontend en `http://localhost:5173` (Vite HMR), backend en `http://localhost:8000`.

---

## 1. Equipos Docentes (`/coordinacion/equipos`)

### Crear
1. Click "Agregar"
2. Seleccionar usuario, materia, carrera, cohorte, rol
3. Llenar fechas de vigencia
4. Submit → debe aparecer en la tabla

### Filtrar
5. Usar filtros de materia, carrera, cohorte, rol
6. Verificar que la tabla se actualiza (llamada a `GET /v1/equipos/` con query params)

### Asignación Masiva
7. Click "Asignación Masiva"
8. Seleccionar múltiples usuarios + materia + rol + desde/hasta
9. Confirmar → debe crear todas las asignaciones

### Clonar Equipo
10. Click "Clonar"
11. Origen: materia + cohorte. Destino: cohorte
12. Confirmar → debe clonar asignaciones

### Vigencia Masiva
13. Click "Vigencia Masiva"
14. Seleccionar materia + cohorte + nuevas fechas
15. Confirmar → debe actualizar vigencias

---

## 2. Encuentros (`/coordinacion/encuentros`)

### Crear Slot Recurrente
1. Seleccionar materia + asignación/docente
2. Título, hora, día de semana, fecha inicio, cantidad de semanas
3. Submit → crea slot + N instancias

### Crear Slot Único
4. Usar "fecha única" en lugar de recurrencia
5. Submit → crea 1 instancia

### Ver/Editar Instancias
6. Tabla muestra Estado (Programado/Realizado/Cancelado), Enlace Meet, Grabación
7. Click en editar → cambiar estado, agregar URLs

---

## 3. Coloquios (`/coordinacion/coloquios`)

### Crear Evaluación
1. Seleccionar materia + cohorte + tipo (Parcial/TP/Coloquio/Recuperatorio)
2. Instancia (ej: "1° Parcial"), días disponibles, cupos
3. Submit → aparece en tabla

### KPIs
4. Las tarjetas de KPIs muestran total convocatorias, reservas activas, resultados, cupos libres

### Filtrar
5. Filtros por materia y cohorte funcionan

---

## 4. Tareas (`/coordinacion/tareas`)

### Crear
1. Click "Nueva Tarea"
2. Título, descripción, prioridad, asignado a, materia
3. Submit → aparece en tabla

### Filtrar
4. Filtro por estado (pendiente/en_progreso/completada)
5. Filtro por materia

### Cambiar Estado
6. Usar el selector de estado en cada fila
7. Verificar que cambia en tabla

---

## 5. Monitor Global (`/coordinacion/monitor`)

### Filtros
1. Filtro por materia
2. Búsqueda por nombre de alumno
3. Rango de fechas
4. Checkbox "Solo atrasados"

### Exportar CSV
5. Click "Exportar CSV" → descarga archivo con datos visibles

---

## 6. Guardias (`/coordinacion/guardias`)

### Crear
1. Click "Agregar"
2. Seleccionar materia, carrera, cohorte, docente
3. Día, horario, fechas de vigencia
4. Submit → aparece en tabla

### Filtrar
5. Filtros por materia, carrera, cohorte, día

### Exportar CSV
6. Click "Exportar CSV" → descarga

---

## 7. Avisos (`/coordinacion/avisos`)

### Crear Aviso
1. Click "Nuevo Aviso"
2. Título, cuerpo, vigencia desde/hasta
3. Scope: TODOS / ROL / USUARIO
4. Si elegís USUARIO → debe mostrar select con nombres reales (no UUID)
5. Submit → aparece en tabla

### Desactivar
6. Click "Desactivar" en un aviso activo → se marca como inactivo

---

## 8. Aprobaciones (`/coordinacion/aprobaciones`)

### Listar por Materia
1. Seleccionar materia en el selector
2. Debe mostrar lotes pendientes de esa materia
3. Cada lote muestra remitente, fecha, cantidad, estado

### Buscar por ID
4. Pegar UUID de lote → muestra detalle

---

## 9. Cuatrimestre (`/coordinacion/cuatrimestre`)

### Paso 1: Materias y Cohortes
1. Se cargan automáticamente materias y cohortes desde la API
2. Checkbox para seleccionar las que corresponden
3. Mínimo 1 materia + 1 cohorte para poder avanzar

### Paso 2: Asignación Docente
4. Cada materia seleccionada muestra:
   - Select de docente (con nombres reales desde API)
   - Select de rol
   - Fecha vigencia desde/hasta
5. Al menos 1 docente asignado para poder avanzar

### Paso 3: Confirmar
6. Resumen con materias, cohortes y asignaciones
7. Click "Confirmar Cuatrimestre"
8. Llama a `POST /v1/equipos/asignacion-masiva` por cada materia
9. Muestra banner verde de éxito o rojo de error

---

## Si algo falla

1. Revisar que el backend esté corriendo: `docker compose ps`
2. Revisar logs del backend: `docker compose logs api`
3. La consola del navegador (F12 → Console) muestra errores de red
4. Los test corren con `npm test` en `frontend/` (74 tests)
