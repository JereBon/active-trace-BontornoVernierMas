# Guía Completa de Flujo — activia-trace

> Plataforma de gestión académica multi-tenant con trazabilidad.
> Backend en `http://localhost:8000`, Frontend en `http://localhost:5173`.

---

## Índice de Roles

| Rol | Secciones |
|-----|-----------|
| **[ADMIN](#1-admin)** | Login, Dashboard, Admin completo, todas las secciones |
| **[PROFESOR](#2-profesor-docente)** | Dashboard, Comisión (padrón, importación, atrasados, comunicaciones, monitor) |
| **[TUTOR](#3-tutor)** | Dashboard, Comisión (atrasados, sin-corregir, monitor) |
| **[COORDINADOR](#4-coordinador)** | Dashboard, Comisión, Coordinación completa (equipos, encuentros, coloquios, tareas, avisos, guardias, cuatrimestre, aprobaciones, monitor global) |
| **[FINANZAS](#5-finanzas)** | Dashboard, Finanzas (periodo, liquidaciones, grilla salarial, facturas, historial) |
| **[NEXO](#6-nexo)** | Dashboard, Comisión (lectura) |

---

## 1. ADMIN

### 1.1 Login

1. Ir a `http://localhost:5173/login`
2. Ingresar email y password
3. Click "Iniciar sesión"
4. ✅ Redirige a `/dashboard` con nombre real en navbar

### 1.2 Dashboard

1. Ver tarjetas de resumen
2. Navegación lateral muestra: Dashboard, Comisión, Coordinación, Finanzas, Admin

### 1.3 Admin — Estructura Académica (`/admin/estructura`)

#### Carreras
1. Click "Agregar" en sección Carreras
2. Completar nombre y código
3. Submit → aparece en tabla con estado "Activa"
4. La tabla muestra nombre, código, estado (Activa/Inactiva)

#### Cohortes
1. Click "Agregar" en sección Cohortes
2. **Select** de carrera (cargado desde API, solo activas)
3. Completar año y plan (opcional)
4. Submit → aparece en tabla con nombre de carrera visible

#### Materias
1. Click "Agregar" en sección Materias
2. Completar nombre, código, categoría clave (opcional)
3. Submit → aparece en tabla

### 1.4 Admin — Usuarios (`/admin/usuarios`)

1. Tabla con todos los usuarios del tenant
2. Columnas: nombre, email, legajo, roles, estado
3. Click en usuario para ver detalle
4. Toggle activo/inactivo

### 1.5 Admin — Auditoría (`/admin/auditoria`)

1. Panel de métricas: total acciones, acciones hoy, acciones por día
2. Top docentes con **nombre real** (no UUID)
3. Log de auditoría paginado con filtros:
   - Filtro por acción (ej: `crear_usuario`)
   - Filtro por fecha desde/hasta
4. Tabla de log: fecha, **actor (nombre real)**, acción, IP

---

## 2. PROFESOR (Docente)

### 2.1 Login y Dashboard

1. Login → `/dashboard`
2. Navbar: Dashboard, Comisión

### 2.2 Comisión — Selector (`/comision`)

1. Lista de materias asignadas al profesor
2. Click en una materia para entrar

### 2.3 Comisión — Padrón (`/comision/:id/padron`)

1. Ver padrón de alumnos de la materia
2. Versiones del padrón (activa + histórico)
3. Importar CSV/XLSX:
   - Subir archivo
   - Preview muestra columnas detectadas
   - Confirmar importación
4. Sincronizar desde Moodle WS

### 2.4 Comisión — Importación (`/comision/:id/importacion`)

1. Importar calificaciones desde LMS:
   - Subir archivo
   - Preview muestra alumnos con notas
   - Seleccionar actividades a importar
   - Confirmar importación
2. Configurar umbral de aprobación:
   - Porcentaje mínimo
   - Valores aprobatorios (ej: "Aprobado", "Promocionado")

### 2.5 Comisión — Atrasados (`/comision/:id/atrasados`)

1. Tabla de estudiantes atrasados según umbral configurado
2. Columnas: nombre, actividades aprobadas/total, porcentaje
3. Paginación (20 por página)
4. Exportar a CSV

### 2.6 Comisión — Sin Corregir (`/comision/:id/sin-corregir`)

1. Tabla de TPs textuales finalizados sin corrección
2. Columnas: alumno, actividad, fecha
3. Paginación

### 2.7 Comisión — Comunicación (`/comision/:id/comunicacion`)

1. Seleccionar destinatarios (atrasados, sin-corregir, o manual)
2. Preview del mensaje renderizado
3. Confirmar envío → se encola
4. Tracking de lote: estado Pendiente → Enviando → Enviado/Error
5. Aprobar/Cancelar lote (si requiere aprobación)

### 2.8 Comisión — Monitor (`/comision/:id/monitor`)

1. Filtros: materia, fecha, búsqueda por nombre
2. Checkbox "Solo atrasados"
3. Tabla de alumnos con progreso
4. Exportar CSV

---

## 3. TUTOR

### 3.1 Login y Dashboard

1. Login → `/dashboard`
2. Navbar: Dashboard, Comisión

### 3.2 Comisión — Acceso

1. `/comision` → lista de materias donde es tutor
2. Puede ver: atrasados, sin-corregir, monitor
3. No puede: importar calificaciones, configurar umbral, enviar comunicaciones

---

## 4. COORDINADOR

### 4.1 Login

1. Login → `/dashboard`
2. Navbar: Dashboard, Comisión, Coordinación

### 4.2 Coordinación — Equipos Docentes (`/coordinacion/equipos`)

#### CRUD Individual
1. Click "Agregar"
2. Seleccionar: **usuario (nombre real)**, materia, carrera, cohorte, rol
3. Fechas de vigencia (desde/hasta)
4. Submit → tabla actualizada
5. Click "Editar" → modificar asignación
6. Click "Eliminar" → soft-delete

#### Filtros
7. Filtrar por materia, carrera, cohorte, rol
8. Tabla con paginación

#### Asignación Masiva
9. Click "Asignación Masiva"
10. Seleccionar múltiples usuarios + materia + rol + vigencia
11. Confirmar → POST /v1/equipos/asignacion-masiva

#### Clonar Equipo
12. Click "Clonar"
13. Origen: materia + cohorte
14. Destino: cohorte
15. Confirmar → clona todas las asignaciones

#### Vigencia Masiva
16. Click "Vigencia Masiva"
17. Materia + cohorte + nuevas fechas
18. Confirmar → actualiza todas

#### Exportar CSV
19. Click "Exportar" → descarga CSV del equipo actual

### 4.3 Coordinación — Encuentros (`/coordinacion/encuentros`)

#### Crear Slot Recurrente
1. Seleccionar materia + asignación/docente
2. Título, hora, día de semana, fecha inicio, cantidad de semanas
3. Submit → crea slot + N instancias

#### Crear Slot Único
4. Usar "fecha única" en lugar de recurrencia
5. Submit → 1 instancia

#### Tabla de Instancias
6. Columnas: fecha, hora, título, estado, enlace Meet, grabación
7. Estados: Programado / Realizado / Cancelado

#### Editar Instancia
8. Click "Editar" → cambiar estado, agregar URLs de Meet/grabación, comentarios

#### Exportar HTML para LMS
9. Generar bloque HTML embeddable

### 4.4 Coordinación — Coloquios (`/coordinacion/coloquios`)

#### KPIs
1. Tarjetas: total convocatorias, reservas activas, resultados, cupos libres

#### Crear Evaluación/Convocatoria
2. Materia + cohorte + tipo (Parcial/TP/Coloquio/Recuperatorio)
3. Instancia, días disponibles, cupos
4. Submit → aparece en tabla

#### Filtrar
5. Filtros por materia y cohorte

#### Gestionar
6. Ver detalle de evaluación
7. Listar/cancelar reservas
8. Registrar resultados

### 4.5 Coordinación — Tareas (`/coordinacion/tareas`)

#### Crear
1. Click "Nueva Tarea"
2. Título, descripción, prioridad, asignado a, materia (opcional)
3. Submit → tabla actualizada

#### Filtrar
4. Filtro por estado (pendiente/en_progreso/completada)
5. Filtro por materia

#### Cambiar Estado
6. Selector de estado en cada fila
7. Transiciones válidas: pendiente→en_progreso→completada

#### Comentarios
8. Click en tarea → ver hilo de comentarios
9. Agregar comentario

#### Delegar
10. Reasignar tarea a otro usuario

### 4.6 Coordinación — Avisos (`/coordinacion/avisos`)

#### Crear
1. Click "Nuevo Aviso"
2. Título, cuerpo
3. Vigencia desde/hasta
4. Scope: TODOS / ROL / USUARIO
5. Si elegís USUARIO → select con **nombres reales**

#### Gestionar
6. Tabla con todos los avisos
7. Click "Desactivar" → toggle activo/inactivo

### 4.7 Coordinación — Guardias (`/coordinacion/guardias`)

#### Crear
1. Click "Agregar"
2. Seleccionar materia, carrera, cohorte, docente
3. Día, horario
4. Fechas de vigencia
5. Submit → tabla actualizada

#### Filtrar
6. Filtros por materia, carrera, cohorte, día

#### Exportar
7. Click "Exportar CSV"

### 4.8 Coordinación — Setup de Cuatrimestre (`/coordinacion/cuatrimestre`)

#### Paso 1: Materias y Cohortes
1. Se cargan desde API automáticamente
2. Checkboxes para seleccionar materias y cohortes
3. Mínimo 1 materia + 1 cohorte

#### Paso 2: Asignación Docente
4. Cada materia seleccionada muestra:
   - Select de **docente (nombres reales)**
   - Select de rol
   - Fecha vigencia desde/hasta
5. Mínimo 1 docente por materia

#### Paso 3: Confirmar
6. Resumen completo
7. Click "Confirmar Cuatrimestre"
8. POST /v1/equipos/asignacion-masiva por cada materia
9. Banner verde de éxito / rojo de error

### 4.9 Coordinación — Aprobaciones (`/coordinacion/aprobaciones`)

1. Selector de materia
2. Lista de lotes de comunicación pendientes
3. Cada lote: remitente, fecha, cantidad, estado
4. Buscar por UUID de lote
5. Aprobar o cancelar lote

### 4.10 Coordinación — Monitor Global (`/coordinacion/monitor`)

1. Filtros: materia, búsqueda por nombre, rango de fechas
2. Checkbox "Solo atrasados"
3. Tabla de rendimiento transversal
4. Exportar CSV

---

## 5. FINANZAS

### 5.1 Login

1. Login → `/dashboard`
2. Navbar: Dashboard, Finanzas

### 5.2 Finanzas — Período (`/finanzas/periodo`)

#### Selección
1. Seleccionar cohorte (UUID por ahora) y período (YYYY-MM)
2. Click "Ver liquidaciones"

#### Vista de Período
3. KPIs: total sin factura, total con factura, cantidad docentes, cantidad NEXOs

#### Calcular Liquidaciones
4. Si no hay datos → botón "Calcular liquidaciones" visible
5. Click → calcula registros

#### Segmentos
6. General: todas las liquidaciones del período
7. NEXO: solo liquidaciones NEXO
8. Facturantes: solo docentes facturantes
9. Columnas: docente, rol, base, plus, total, estado (Abierta/Cerrada)

#### Cerrar Período
10. Si hay liquidaciones abiertas → botón "Cerrar período"
11. Confirmar en modal
12. ✅ No se puede deshacer

### 5.3 Finanzas — Historial (`/finanzas/historial`)

1. Lista de períodos cerrados
2. Filtros por cohorte y período

### 5.4 Finanzas — Grilla Salarial (`/finanzas/grilla`)

#### Salario Base
1. Tabla con roles y montos base
2. Click "Agregar" → nuevo salario base (rol, monto, vigencia)
3. Click "Editar"

#### Salario Plus
4. Tabla con grupos y montos plus
5. Click "Agregar" → nuevo plus (grupo, rol, monto, vigencia)
6. Click "Editar"

### 5.5 Finanzas — Facturas (`/finanzas/facturas`)

#### Listar
1. Tabla con filtros por estado y período
2. Columnas: docente, período, monto, N° factura, emisión, estado

#### Crear Factura
3. Click "+ Nueva factura"
4. Modal con: usuario ID, período, monto, N° factura (opcional), fecha emisión (opcional)
5. Submit → factura creada

#### Cambiar Estado
6. Factura pendiente → botón "Marcar abonada"
7. Cambia estado a "abonada"

---

## 6. NEXO

### 6.1 Acceso

1. Login → `/dashboard`
2. Navbar: Dashboard, Comisión (solo lectura)

### 6.2 Limitaciones

- NEXO puede ver comisiones pero **no** tiene permisos de escritura
- No puede importar, configurar umbrales, ni enviar comunicaciones
- Puede ver monitor y atrasados
- Aparece en segmento "NEXO" de liquidaciones

---

## 7. Flujos Transversales

### 7.1 Autenticación

| Paso | Descripción |
|------|-------------|
| Login | Email + password → JWT access + refresh |
| Silent Refresh | Al recargar, refresh token rotado automáticamente |
| Logout | Revoca refresh token, limpia sesión |
| 2FA | ⏳ **Placeholder** (backend listo, frontend pendiente) |
| Forgot Password | ⏳ **No implementado** (backend listo) |
| Reset Password | ⏳ **No implementado** (backend listo) |

### 7.2 Seguridad

- JWT con access corto + refresh rotation
- Argon2id para passwords
- AES-256 para PII (CBU, DNI, CUIL)
- Multi-tenancy row-level en todas las queries
- RBAC con permisos finos `modulo:accion`
- Auditoría append-only en todas las operaciones
- Soft-delete en todas las entidades

---

## 8. Flujo de Datos E2E

```
1. ADMIN crea estructura académica
   ├── Carreras → Cohortes → Materias
   └── Usuarios + roles

2. COORDINADOR arma equipos docentes
   ├── Asignación individual / masiva
   ├── Clonar equipos entre cohortes
   └── Setup de cuatrimestre (wizard)

3. PROFESOR importa datos
   ├── Padrón de alumnos (CSV/XLSX/Moodle WS)
   ├── Calificaciones desde LMS
   └── Configura umbral de aprobación

4. PROFESOR analiza y comunica
   ├── Atrasados / Sin corregir / Ranking
   ├── Envía comunicaciones a atrasados
   └── Tracking de envío en tiempo real

5. COORDINADOR gestiona operación diaria
   ├── Encuentros (slots recurrentes + instancias)
   ├── Coloquios (convocatorias + reservas + resultados)
   ├── Guardias (registro y consulta)
   ├── Tareas (asignación + workflow)
   ├── Avisos (publicación con scope)
   └── Monitor global transversal

6. FINANZAS liquida
   ├── Calcula liquidaciones del período
   ├── Grilla salarial (base + plus)
   ├── Gestión de facturas
   └── Cierre de período

7. ADMIN audita
   ├── Log completo de operaciones
   ├── Métricas de uso
   └── Trazabilidad multi-tenant
```

---

## 9. Testing

```bash
# Frontend (74 tests, 20 archivos)
cd frontend && npm test

# Backend (31 archivos de test)
cd backend && pytest
```
