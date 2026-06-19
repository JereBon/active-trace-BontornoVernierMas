# Trabajo Pendiente — activia-trace

> Estado al 18-Jun-2026. Backend 100% completo. Frontend 100% completo.

---

## 1. CHANGES.md — Actualizado

✅ Los 24 changes están marcados como `[x]` completados.

---

## 2. Frontend — Estado General

### Auth Flows (GRUPO 1) — ✅ COMPLETO

| Página | Endpoints Backend | Estado |
|--------|------------------|--------|
| **Login** | `POST /api/auth/login` | ✅ |
| **2FA Verify** | `POST /api/auth/2fa/verify` | ✅ Real, no placeholder |
| **2FA Enroll** | `POST /api/auth/2fa/enroll` + `/confirm` | ✅ QR + secret + confirm |
| **Forgot Password** | `POST /api/auth/forgot` | ✅ |
| **Reset Password** | `POST /api/auth/reset` | ✅ Lee token de URL |
| **Impersonation** | `POST /api/auth/impersonate` + `/end` | ✅ Banner + botón en admin |

### Perfil e Inbox (GRUPO 2) — ✅ COMPLETO

| Página | Endpoints Backend | Estado |
|--------|------------------|--------|
| **Ver Perfil** | `GET /v1/perfil` | ✅ Datos reales |
| **Editar Perfil** | `PATCH /v1/perfil` | ✅ Inline, múltiples campos |
| **Subir factura propia** | `POST /v1/facturas/mias` | ✅ Formulario en perfil cuando `facturador=true` |
| **Inbox (Bandeja)** | `GET /v1/inbox/` | ✅ Split-panel con tabs |
| **Mensajes Enviados** | `GET /v1/inbox/enviados` | ✅ Tab en inbox |
| **Enviar Mensaje** | `POST /v1/inbox/` | ✅ Modal con validación |
| **Responder Mensaje** | `POST /v1/inbox/{id}/responder` | ✅ Inline en detalle |

### Programas y Fechas (GRUPO 3) — ✅ COMPLETO

| Página | Endpoints Backend | Estado |
|--------|------------------|--------|
| **Programas** | `GET/POST /v1/programas` + DELETE | ✅ Tabla + form inline |
| **Fechas Académicas** | `GET/POST/DELETE /v1/fechas-academicas` | ✅ Tabla + form con filtros |

### Funcionalidades nuevas (HU-04, HU-28, HU-47, HU-49) — ✅ COMPLETO

| Funcionalidad | Qué se implementó | Estado |
|---------------|-------------------|--------|
| **HU-04 — Vaciar datos de materia** | Botón "Vaciar datos" + confirm dialog en PadronPage. Backend endpoint ya existía. | ✅ |
| **HU-28 — Exportar encuentros HTML** | Botón "Exportar HTML" en EncuentrosPage. Backend endpoint ya existía. | ✅ |
| **HU-47 — Alumno reserva coloquio** | Nuevo endpoint `GET /v1/coloquios/disponibles` + `GET /v1/coloquios/mis-reservas` + repository method. Frontend: `ColoquiosAlumnoPage` + ruta `/alumno/coloquios` + card en dashboard. | ✅ |
| **HU-49 — Docente sube factura** | Nuevo permiso `facturas:subir_propias`. Nuevos endpoints `POST/GET /v1/facturas/mias`. RBAC: PROFESOR y TUTOR ahora pueden subir facturas. Frontend: sección "Mis facturas" en PerfilPage cuando `facturador=true`. | ✅ |
| **HU-46 — Registrar guardia** | Ya estaba implementado: GuardiasPage con formulario completo, backend POST listo, TUTOR tiene permiso `guardias:registrar`. | ✅ Ya existía |

---

## 3. Mejoras y Tests (GRUPO 4) — ✅ COMPLETO

| Issue | Estado |
|-------|--------|
| **Tests de auth** (`features/auth/__tests__/`) | ✅ 2 suites: authService (9 tests), AuthGuard (5 tests) |
| **Tests de dashboard** (`features/dashboard/__tests__/`) | ✅ 7 tests de render por rol |
| **PeriodoPage UUID** | ✅ Reemplazado por select de cohortes |
| **Rutas de perfil/inbox** | ✅ En AppShell + App.tsx |

---

## 4. Code Smells Limpiados

| Ítem | Acción |
|------|--------|
| `app/core/permissions.py` (placeholder muerto de C-04) | 🗑️ Eliminado |
| `app/workers/main.py` (placeholder no-op no usado) | 🗑️ Eliminado |

---

## 5. Backend 100% Completo

```yaml
Routers: 23/23 ✅
Models: 32/32 ✅
Schemas: ~60 ✅
Migrations: 17/17 ✅
Workers: 1 (comunicacion_worker real) ✅
Tests: 29 archivos ✅
Permisos RBAC: 25 módulo:accion ✅
```
