# Testing Checklist — activia-trace

> Checklist exhaustiva para probar **cada funcionalidad** del sistema con **cada rol**.
> Formato: `[ ]` pendiente · `[x]` aprobado · `[~]` requiere fix (anotar detalle)

---

## 🌐 PRE-FLIGHT (global, cualquier sesión)

- [x] **PF-01**: La app carga sin errores de consola (F12 → Console)
- [x] **PF-02**: No hay errores 404 en rutas conhecidas
- [x] **PF-03**: El layout responsive funciona (mobile 375px, tablet 768px, desktop 1440px)
- [x] **PF-04**: Los loading spinners aparecen mientras cargan datos
- [x] **PF-05**: Los estados vacíos muestran mensaje informativo ("No hay datos")
- [x] **PF-06**: Los errores HTTP (4xx/5xx) muestran mensaje al usuario, no pantalla en blanco
- [x] **PF-07**: Todos los botones tienen estado `disabled` mientras la acción está en curso

---

## 🔐 SESIÓN ANÓNIMA (sin login)

### Login Page (`/login`)

- [x] **AUTH-01**: Muestra formulario de email + password
- [x] **AUTH-02**: Email inválido muestra error de validación
- [x] **AUTH-03**: Campos vacíos muestra error de validación
- [x] **AUTH-04**: Password incorrecto muestra error "Credenciales inválidas"
- [x] **AUTH-05**: Login exitoso redirige a `/dashboard`
- [x] **AUTH-06**: Login exitoso guarda sesión (recargar página no pierde sesión)
- [x] **AUTH-07**: Link "Olvidé mi contraseña" navega a `/forgot-password`
- [x] **AUTH-08**: Intentar acceder a `/dashboard` sin sesión redirige a `/login`

### Forgot Password (`/forgot-password`)

- [x] **AUTH-09**: Muestra campo de email
- [x] **AUTH-10**: Email no registrado muestra mensaje genérico (no revela existencia)
- [x] **AUTH-11**: Email registrado muestra "Revisá tu correo"
- [x] **AUTH-12**: Link "Volver al login" funciona

### Reset Password (`/reset-password`)

- [x] **AUTH-13**: Muestra campos password + confirmar password
- [x] **AUTH-14**: Token inválido/expirado muestra error
- [x] **AUTH-15**: Password no coincide con confirmación muestra error
- [x] **AUTH-16**: Reset exitoso muestra mensaje y link a login

---

## 👤 ROL ADMIN

### Login como ADMIN

- [x] **ADM-01**: Login exitoso redirige a `/dashboard`
- [x] **ADM-02**: Dashboard muestra cards: Comisión, Coordinación, Administración (NO Finanzas, NO Coloquios alumno)
- [x] **ADM-03**: Sidebar/AppShell muestra links: Dashboard, Mi Perfil, Mensajes, Comisión, Coordinación, Administración

### Dashboard

- [x] **ADM-04**: Card "Comisión" → navega a `/comision`
- [x] **ADM-05**: Card "Coordinación" → navega a `/coordinacion`
- [x] **ADM-06**: Card "Administración" → navega a `/admin`

### Perfil (`/perfil`)

- [x] **ADM-07**: Muestra datos del usuario: nombre, email, CUIL, legajo, regional, roles
- [x] **ADM-08**: Botón "Editar" permite modificar nombre, apellidos, regional, banco, CBU, alias
- [x] **ADM-09**: Checkbox "Emito factura" se guarda correctamente
- [x] **ADM-10**: Botón "Configurar 2FA" navega a `/perfil/2fa`
- [x] **ADM-11**: SI `facturador=true`: se ve sección "Mis facturas" con tabla y botón "Subir factura"
- [x] **ADM-12**: "Subir factura": ingresar período (AAAA-MM) + detalle → se crea factura con estado Pendiente
- [x] **ADM-13**: Factura subida aparece en la tabla con estado "Pendiente" badge amarillo

### 2FA (`/perfil/2fa`)

- [x] **ADM-14**: Muestra QR + código manual + campo para confirmar
- [x] **ADM-15**: Escanear QR con app TOTP funciona
- [x] **ADM-16**: Ingresar código TOTP incorrecto muestra error
- [x] **ADM-17**: Confirmar código correcto muestra "2FA activado"
- [x] **ADM-18**: Cerrar sesión y volver a login → pide código 2FA después de password

### Inbox (`/inbox`)

- [x] **ADM-19**: Panel izquierdo con tabs "Recibidos" / "Enviados"
- [x] **ADM-20**: Lista de mensajes recibidos se muestra correctamente
- [x] **ADM-21**: Click en mensaje → panel derecho muestra detalle
- [x] **ADM-22**: Botón "Responder" en detalle → muestra form inline
- [x] **ADM-23**: Enviar respuesta → mensaje se agrega al hilo (FIX: backend incluye respuestas)
- [x] **ADM-24**: Tab "Enviados" muestra mensajes enviados
- [x] **ADM-25**: Botón "Redactar" → modal con selector de usuarios (reemplacé UUID por buscador)
- [x] **ADM-26**: Modal "Redactar": campos requeridos validados
- [x] **ADM-27**: Enviar mensaje desde modal → mensaje aparece en "Enviados"

### Comisión (`/comision`)

- [ ] **ADM-28**: Index `/comision` pide seleccionar materia (o redirect a primera)
- [ ] **ADM-29**: Layout comisión tiene tabs: Padrón, Importación, Atrasados, Sin Corregir, Comunicación, Monitor

#### Padrón (`/comision/:id/padron`)

- [ ] **ADM-30**: Selector de cohorte funciona
- [ ] **ADM-31**: Subir archivo CSV/XLSX → muestra vista previa con columnas
- [ ] **ADM-32**: Confirmar vista previa → padrón importado, versión activa creada
- [ ] **ADM-33**: Historial de versiones visible debajo
- [ ] **ADM-34**: Botón "Vaciar datos" → modal de confirmación
- [ ] **ADM-35**: Confirmar vaciado → versión e entradas eliminadas, historial vacío
- [ ] **ADM-36**: Versión activa con badge verde, inactivas con gris

#### Importación (`/comision/:id/importacion`)

- [ ] **ADM-37**: Subir archivo de calificaciones → vista previa con actividades detectadas
- [ ] **ADM-38**: Selector de actividades permite elegir cuáles importar
- [ ] **ADM-39**: Confirmar importación → datos cargados
- [ ] **ADM-40**: Umbral configurable (default 60%), se guarda correctamente

#### Atrasados (`/comision/:id/atrasados`)

- [ ] **ADM-41**: Muestra tabla de alumnos atrasados (actividades faltantes o < umbral)
- [ ] **ADM-42**: Mensaje positivo si no hay atrasados

#### Sin Corregir (`/comision/:id/sin-corregir`)

- [ ] **ADM-43**: Muestra entregas sin corregir detectadas
- [ ] **ADM-44**: Botón de exportar funciona

#### Comunicación (`/comision/:id/comunicacion`)

- [ ] **ADM-45**: Formulario de redacción con preview
- [ ] **ADM-46**: Preview muestra asunto y cuerpo renderizados
- [ ] **ADM-47**: Enviar → tracking de estado en tiempo real (Pendiente → Enviando → Enviado)
- [ ] **ADM-48**: Panel de tracking con estados visibles

#### Monitor (`/comision/:id/monitor`)

- [ ] **ADM-49**: Filtros: materia, alumno, estado, comisión, regional
- [ ] **ADM-50**: Tabla con datos filtrados
- [ ] **ADM-51**: Exportar CSV funciona

### Coordinación (`/coordinacion`)

- [ ] **ADM-52**: Default redirect a `/coordinacion/equipos`
- [ ] **ADM-53**: Sidebar/tabs: Equipos, Avisos, Tareas, Programas, Fechas, Monitor, Encuentros, Coloquios, Cuatrimestre, Guardias, Aprobaciones

#### Equipos

- [ ] **ADM-54**: Tabla de equipos con filtros (materia, carrera, cohorte, rol, estado)
- [ ] **ADM-55**: Botón "Nuevo" → formulario de asignación
- [ ] **ADM-56**: Asignación masiva: seleccionar múltiples docentes
- [ ] **ADM-57**: Clonar equipo entre cohortes
- [ ] **ADM-58**: Modificar vigencia en bloque
- [ ] **ADM-59**: Exportar equipo a CSV

#### Avisos

- [ ] **ADM-60**: Tabla de avisos publicados
- [ ] **ADM-61**: Botón "Nuevo aviso" → formulario con alcance, severidad, vigencia, require_ack
- [ ] **ADM-62**: Filtros por alcance o estado
- [ ] **ADM-63**: Contadores de vistos y acuses visibles

#### Tareas

- [ ] **ADM-64**: Tabla de tareas con filtros (asignado, asignador, materia, estado)
- [ ] **ADM-65**: Botón "Nueva tarea" → form con asignación
- [ ] **ADM-66**: Click en tarea → detalle con hilo de comentarios
- [ ] **ADM-67**: Cambiar estado + agregar comentario
- [ ] **ADM-68**: Delegar tarea a otro docente

#### Programas

- [ ] **ADM-69**: Tabla con programas filtrable por materia
- [ ] **ADM-70**: Botón "Nuevo programa" → form con materia + título + archivo
- [ ] **ADM-71**: Eliminar programa con confirmación

#### Fechas

- [ ] **ADM-72**: Tabla de fechas con filtro por materia
- [ ] **ADM-73**: Badges de colores por tipo (Parcial/TP/Coloquio)
- [ ] **ADM-74**: Botón "Nueva fecha" → form con materia, tipo, instancia, fecha, cohorte
- [ ] **ADM-75**: Eliminar fecha con confirmación

#### Monitor Global

- [ ] **ADM-76**: Filtros: materia, regional, comisión, búsqueda, estado, rango fechas
- [ ] **ADM-77**: Tabla con datos del monitor general
- [ ] **ADM-78**: Exportar CSV

#### Encuentros

- [ ] **ADM-79**: Tabla de encuentros/instancias
- [ ] **ADM-80**: Botón "Nuevo Encuentro" → form con slot recurrente o único
- [ ] **ADM-81**: Crear encuentro recurrente → genera N instancias
- [ ] **ADM-82**: Editar instancia individual (estado, meet_url, video_url, comentario)
- [ ] **ADM-83**: Botón "Exportar HTML" → descarga archivo .html con tabla de encuentros

#### Coloquios (gestión)

- [ ] **ADM-84**: KPIs: convocatorias activas, cupos libres, reservas activas, notas
- [ ] **ADM-85**: Tabla de convocatorias
- [ ] **ADM-86**: Botón "Nueva Convocatoria" → form con materia, instancia, días, cupos
- [ ] **ADM-87**: Editar / Eliminar convocatoria
- [ ] **ADM-88**: Ver reservas de cada convocatoria

#### Cuatrimestre

- [ ] **ADM-89**: Setup wizard/stepper para nuevo cuatrimestre
- [ ] **ADM-90**: Paso: seleccionar materias y cohortes
- [ ] **ADM-91**: Paso: asignar equipos docentes
- [ ] **ADM-92**: Resumen antes de confirmar

#### Guardias

- [ ] **ADM-93**: Tabla de guardias con filtros (materia, carrera, cohorte, estado)
- [ ] **ADM-94**: Botón "Registrar Guardia" → formulario completo
- [ ] **ADM-95**: Selectores anidados: Materia → Carrera → Cohorte → Asignación
- [ ] **ADM-96**: Crear guardia → aparece en tabla
- [ ] **ADM-97**: Exportar CSV

#### Aprobaciones

- [ ] **ADM-98**: Lista de comunicaciones pendientes de aprobación
- [ ] **ADM-99**: Botón "Aprobar" → cambia estado a Enviado
- [ ] **ADM-100**: Botón "Cancelar" → cambia estado a Cancelado

### Administración (`/admin`)

#### Estructura (`/admin/estructura`)

- [ ] **ADM-101**: Secciones: Carreras, Cohortes, Materias
- [ ] **ADM-102**: ABM Carreras: crear, editar, desactivar
- [ ] **ADM-103**: ABM Cohortes: crear, editar, desactivar
- [ ] **ADM-104**: ABM Materias: crear, editar, desactivar (con categoría_clave para Plus)
- [ ] **ADM-105**: Validaciones: código único por tenant, carrera inactiva no permite cohortes

#### Usuarios (`/admin/usuarios`)

- [ ] **ADM-106**: Tabla de usuarios con búsqueda
- [ ] **ADM-107**: Botón "Nuevo usuario" → form completo (nombre, DNI, CUIL, banco, CBU, regional, email, roles)
- [ ] **ADM-108**: Editar usuario
- [ ] **ADM-109**: Activar / Desactivar usuario
- [ ] **ADM-110**: Botón "Impersonar" → se activa banner naranja "Impersonando a..."
- [ ] **ADM-111**: Durante impersonación: todas las acciones se registran a nombre del admin original
- [ ] **ADM-112**: Botón "Salir de impersonación" en banner

#### Auditoría (`/admin/auditoria`)

- [ ] **ADM-113**: Panel de interacciones: acciones por día, estado comunicaciones por docente
- [ ] **ADM-114**: Log completo de auditoría con filtros: rango fechas, materia, usuario, acción
- [ ] **ADM-115**: Cada entrada muestra: timestamp, usuario, materia, acción, IP, user-agent

---

## 👨‍🏫 ROL PROFESOR

### Login como PROFESOR

- [ ] **PROF-01**: Login exitoso redirige a `/dashboard`
- [ ] **PROF-02**: Dashboard muestra cards: Comisión (NO Coordinación, NO Admin)
- [ ] **PROF-03**: AppShell muestra: Dashboard, Mi Perfil, Mensajes, Comisión

### Perfil

- [ ] **PROF-04**: Mismos campos que ADMIN (nombre, email, CUIL, etc.)
- [ ] **PROF-05**: Checkbox "Emito factura" → muestra sección "Mis facturas"
- [ ] **PROF-06**: Subir factura propia → endpoint `POST /v1/facturas/mias`
- [ ] **PROF-07**: Factura subida visible en tabla con estado "Pendiente"
- [ ] **PROF-08**: Configurar 2FA funciona
- [ ] **PROF-09**: LOGOUT → sesión cerrada, redirect a login

### Inbox

- [ ] **PROF-10**: Bandeja de entrada funcional (recibidos + enviados)
- [ ] **PROF-11**: Redactar mensaje a otro usuario
- [ ] **PROF-12**: Responder a hilo

### Comisión

- [ ] **PROF-13**: Importar calificaciones con preview
- [ ] **PROF-14**: Configurar umbral de aprobación
- [ ] **PROF-15**: Ver atrasados
- [ ] **PROF-16**: Ver ranking de alumnos
- [ ] **PROF-17**: Ver notas finales
- [ ] **PROF-18**: Exportar TPs sin corregir
- [ ] **PROF-19**: Enviar comunicación con preview
- [ ] **PROF-20**: Monitor de seguimiento (solo sus alumnos)
- [ ] **PROF-21**: Importar padrón de alumnos
- [ ] **PROF-22**: Botón "Vaciar datos" en padrón (pero puede NO tener permiso según RBAC — ver ADM-34)

### NO debe ver

- [ ] **PROF-23**: NO ve card/ruta de Coordinación
- [ ] **PROF-24**: NO ve card/ruta de Administración
- [ ] **PROF-25**: NO ve card/ruta de Finanzas

---

## 👩‍🏫 ROL TUTOR

### Login como TUTOR

- [ ] **TUT-01**: Login exitoso redirige a `/dashboard`
- [ ] **TUT-02**: Dashboard muestra cards: Comisión
- [ ] **TUT-03**: Ver atrasados (solo lectura)
- [ ] **TUT-04**: Ver entregas sin corregir
- [ ] **TUT-05**: Monitor de seguimiento (solo sus alumnos asignados)
- [ ] **TUT-06**: Guardias → Registrar guardia (formulario completo)
- [ ] **TUT-07**: Perfil con "Mis facturas" si facturador=true
- [ ] **TUT-08**: Inbox funcional

### NO debe ver

- [ ] **TUT-09**: NO puede importar calificaciones
- [ ] **TUT-10**: NO puede enviar comunicaciones
- [ ] **TUT-11**: NO ve Coordinación/Admin/Finanzas

---

## 🧑‍💼 ROL COORDINADOR

### Login como COORDINADOR

- [ ] **COOR-01**: Dashboard muestra cards: Comisión, Coordinación
- [ ] **COOR-02**: Acceso completo a `/coordinacion/*`

### Coordinación (todo lo que ADMIN ve en coordinación)

- [ ] **COOR-03**: Equipos: ver, asignar, clonar, modificar vigencia, exportar
- [ ] **COOR-04**: Avisos: publicar, editar, ver contadores de ack
- [ ] **COOR-05**: Tareas: crear, asignar, cambiar estado, comentar
- [ ] **COOR-06**: Programas: ABM completo
- [ ] **COOR-07**: Fechas: ABM completo
- [ ] **COOR-08**: Monitor global con filtros
- [ ] **COOR-09**: Encuentros: crear slots, editar instancias, exportar HTML
- [ ] **COOR-10**: Coloquios: crear convocatorias, ver métricas, ver reservas, registrar resultados
- [ ] **COOR-11**: Cuatrimestre: setup wizard
- [ ] **COOR-12**: Guardias: ver todas, registrar, exportar CSV
- [ ] **COOR-13**: Aprobaciones: aprobar/cancelar comunicaciones pendientes

### NO debe ver

- [ ] **COOR-14**: NO ve card de Administración
- [ ] **COOR-15**: NO ve card de Finanzas
- [ ] **COOR-16**: NO puede gestionar usuarios (solo ver en contexto de equipos)

---

## 💰 ROL FINANZAS

### Login como FINANZAS

- [ ] **FIN-01**: Dashboard muestra cards: Finanzas
- [ ] **FIN-02**: AppShell muestra: Dashboard, Mi Perfil, Mensajes, Finanzas

### Finanzas (`/finanzas`)

- [ ] **FIN-03**: Periodo: vista de liquidación del período con segmentación (General / NEXO / Factura)
- [ ] **FIN-04**: KPIs: Total sin factura, Total con factura
- [ ] **FIN-05**: Cerrar liquidación → confirmación → estado Cerrada (inmutable)
- [ ] **FIN-06**: Historial de liquidaciones cerradas
- [ ] **FIN-07**: Grilla salarial: ABM salario base por rol + vigencia
- [ ] **FIN-08**: Grilla salarial: ABM plus por clave + rol + vigencia
- [ ] **FIN-09**: Facturas: listado de facturas de docentes con filtros
- [ ] **FIN-10**: Crear factura (admin) para un docente
- [ ] **FIN-11**: Marcar factura como "Abonada"

### NO debe ver

- [ ] **FIN-12**: NO ve card de Comisión
- [ ] **FIN-13**: NO ve card de Coordinación
- [ ] **FIN-14**: NO ve card de Administración

---

## 🎓 ROL ALUMNO

### Login como ALUMNO

- [ ] **ALU-01**: Login exitoso redirige a `/dashboard`
- [ ] **ALU-02**: Dashboard muestra card: Coloquios
- [ ] **ALU-03**: AppShell muestra: Dashboard, Mi Perfil

### Coloquios (`/alumno/coloquios`)

- [ ] **ALU-04**: Sección "Convocatorias abiertas" muestra coloquios disponibles
- [ ] **ALU-05**: Cada coloquio muestra: instancia, cupos disponibles, tipo
- [ ] **ALU-06**: Botón "Reservar" → selector de fecha/hora
- [ ] **ALU-07**: Reservar con fecha válida → reserva creada
- [ ] **ALU-08**: Reservar sin cupos → error "Sin cupos disponibles"
- [ ] **ALU-09**: Reservar cuando ya hay reserva activa → error "Ya existe una reserva activa"
- [ ] **ALU-10**: Sección "Mis reservas" muestra reservas activas
- [ ] **ALU-11**: Botón "Cancelar" en reserva activa → estado cambia a Cancelada
- [ ] **ALU-12**: Cancelar restaura cupo disponible

### Perfil

- [ ] **ALU-13**: Ver perfil (datos personales)
- [ ] **ALU-14**: Editar perfil

### NO debe ver

- [ ] **ALU-15**: NO ve card de Comisión
- [ ] **ALU-16**: NO ve card de Coordinación
- [ ] **ALU-17**: NO ve card de Administración
- [ ] **ALU-18**: NO ve card de Finanzas
- [ ] **ALU-19**: NO ve Inbox (si aplica)

---

## 📧 MAILHOG / EMAIL DELIVERY

- [ ] **MH-01**: Mailhog web UI accesible en `http://localhost:8025`
- [ ] **MH-02**: Solicitar reset de password → email aparece en Mailhog
- [ ] **MH-03**: Email de reset contiene link con token válido
- [ ] **MH-04**: Hacer clic en link del email → abre reset-password con token precargado
- [ ] **MH-05**: Comunicación masiva (desde comisión) → email aparece en Mailhog con asunto y cuerpo correctos
- [ ] **MH-06**: Email de comunicación contiene variables reemplazadas (ej: `{{alumno.nombre}}` → nombre real)
- [ ] **MH-07**: Mailhog persiste emails entre reinicios de contenedor (opcional)
- [ ] **MH-08**: Cambiar `EMAIL_BACKEND=stub` → emails se loguean pero NO aparecen en Mailhog

## 🔄 FLUJOS TRANSVERSALES

### Impersonación (ADMIN → cualquier rol)

- [ ] **IMP-01**: ADMIN ve botón "Impersonar" en usuarios activos
- [ ] **IMP-02**: Click "Impersonar" → confirm dialog → banner naranja aparece
- [ ] **IMP-03**: Durante impersonación: ve dashboard del rol impersonado
- [ ] **IMP-04**: Durante impersonación: puede navegar como ese rol
- [ ] **IMP-05**: Botón "Salir de impersonación" → vuelve a sesión ADMIN
- [ ] **IMP-06**: Audit log registra ambas identidades (actor real + impersonado)

### Multi-tenancy

- [ ] **MT-01**: Crear dos tenants distintos
- [ ] **MT-02**: Usuario del Tenant A NO ve datos del Tenant B
- [ ] **MT-03**: Usuario del Tenant A NO puede acceder a recursos del Tenant B

### Soft Delete

- [ ] **SD-01**: Eliminar un registro → NO desaparece de DB (deleted_at seteado)
- [ ] **SD-02**: Registro eliminado NO aparece en UI
- [ ] **SD-03**: Audit log registra la eliminación

### Refresh Token

- [ ] **REF-01**: Sesión activa después de 15 min → refresh automático (sin perder datos)
- [ ] **REF-02**: Cerrar sesión → refresh token invalidado
- [ ] **REF-03**: Refresh token reusado → ambos tokens invalidados (rotation)

---

## 🧪 FLUJOS CRÍTICOS E2E

### FL-01: Setup completo de cuatrimestre

- [ ] **E2E-01**: ADMIN crea carrera → cohorte → materia (estructura académica)
- [ ] **E2E-02**: COORDINADOR asigna docentes a la materia (equipos)
- [ ] **E2E-03**: COORDINADOR programa fechas de evaluación
- [ ] **E2E-04**: COORDINADOR sube programa de materia
- [ ] **E2E-05**: PROFESOR importa padrón de alumnos
- [ ] **E2E-06**: PROFESOR importa calificaciones
- [ ] **E2E-07**: PROFESOR ve atrasados
- [ ] **E2E-08**: PROFESOR envía comunicación a atrasados (con preview + tracking)
- [ ] **E2E-09**: COORDINADOR aprueba la comunicación (si aplica aprobación)
- [ ] **E2E-10**: PROFESOR registra encuentros recurrentes
- [ ] **E2E-11**: TUTOR registra guardias
- [ ] **E2E-12**: FINANZAS calcula y cierra liquidación del período

### FL-02: Coloquio

- [ ] **E2E-13**: COORDINADOR crea convocatoria de coloquio con cupos
- [ ] **E2E-14**: ALUMNO ve coloquio disponible y reserva turno
- [ ] **E2E-15**: ALUMNO cancela reserva
- [ ] **E2E-16**: COORDINADOR registra nota del coloquio

### FL-03: Facturación

- [ ] **E2E-17**: PROFESOR marca "Emito factura" en perfil
- [ ] **E2E-18**: PROFESOR sube factura desde perfil
- [ ] **E2E-19**: FINANZAS ve la factura en `/finanzas/facturas`
- [ ] **E2E-20**: FINANZAS marca la factura como "Abonada"

### FL-04: Aviso + Acknowledgment

- [ ] **E2E-21**: COORDINADOR publica aviso con require_ack=true
- [ ] **E2E-22**: PROFESOR ve el aviso en su dashboard/sidebar
- [ ] **E2E-23**: PROFESOR confirma lectura (ack)
- [ ] **E2E-24**: COORDINADOR ve contador de acks incrementado

---

## ⚠️ CASOS BORDE

- [ ] **EDGE-01**: Sesión expirada mientras se escribe un formulario → redirect a login sin perder datos
- [ ] **EDGE-02**: Subir archivo vacío → error controlado
- [ ] **EDGE-03**: Subir archivo de formato incorrecto → error controlado
- [ ] **EDGE-04**: Hacer clic rápido múltiple en botón "Enviar" → solo 1 request
- [ ] **EDGE-05**: Navegación directa a URL inexistente → redirect a dashboard
- [ ] **EDGE-06**: 2FA: intentar login con código TOTP expirado → error
- [ ] **EDGE-07**: 2FA: reintentar login con 2FA correcto después de varios fallos → ok

---

## 📊 RESUMEN DE COBERTURA

| Rol | Tests esperados |
|-----|----------------|
| Anónimo / Pre-auth | 16 |
| ADMIN | ~115 |
| PROFESOR | 25 |
| TUTOR | 11 |
| COORDINADOR | 16 |
| FINANZAS | 14 |
| ALUMNO | 19 |
| Transversales | 10 |
| E2E | 24 |
| Casos borde | 7 |
| **TOTAL** | **~257** |
