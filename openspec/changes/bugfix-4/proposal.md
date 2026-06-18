## Why

Tras la implementación de los changes C-22 (frontend-academico-docente), C-23 (frontend-coordinacion) y C-24 (frontend-finanzas-y-admin), se identificaron 9 issues críticos/altos en una auditoría integral del proyecto. Estos incluyen gaps de seguridad (AuthGuard sin role checking, hard-delete), datos incorrectos en UI (Navbar sin nombre real, actor_id como UUID crudo), formularios con UX deficiente (UUID manual en cohorte), features backend sin frontend (crear factura, calcular liquidaciones), y documentación desactualizada (CHANGES.md). Este change unifica todas las correcciones en un solo batch.

## What Changes

- AuthGuard ahora acepta `requiredRoles` y redirige a `/dashboard` si no tiene el rol
- Las rutas en App.tsx se protegen por rol: ADMIN, COORDINADOR, FINANZAS, PROFESOR/TUTOR
- `deleteCarrera` cambia de DELETE HTTP a PATCH `{ activa: false }` (soft-delete)
- `useAuth.ts` ahora llama `getMeApi()` tras login y refresh para obtener `full_name` y `email` reales
- CHANGES.md marca C-22, C-23, C-24 como `[x]` completo
- Zod schemas en EstructuraAcademica agregan `.strict()` para rechazar campos extra
- Formulario de Cohorte reemplaza input UUID manual por `<select>` con carreras activas
- PanelAuditoria muestra nombre del usuario en vez de `actor_id` UUID crudo
- TablaFacturas agrega modal "Nueva factura" con conexión a `createFactura`
- VistaPeriodo agrega botón "Calcular liquidaciones" cuando no hay datos

## Capabilities

### New Capabilities
- `role-guard`: Protección de rutas por rol en frontend
- `factura-create-ui`: UI de creación de facturas
- `liquidacion-calcular-ui`: Botón para calcular liquidaciones desde la UI

### Modified Capabilities
- `estructura-academica`: Zod schemas con `.strict()`, soft-delete en carreras, select de carreras en cohorte
- `frontend-auth`: AuthGuard con verificación de roles, `getMeApi` en flujo de login/refresh
- `auditoria-panel`: Muestra nombre del usuario en lugar de UUID en log y top docentes

## Impact

- **Frontend**: 12+ componentes modificados (AuthGuard, App.tsx, EstructuraAcademica, PanelAuditoria, TablaFacturas, VistaPeriodo, useAuth, estructuraService, etc.)
- **Backend**: Ningún cambio — todo es frontend + documentación
- **Documentación**: CHANGES.md actualizado con estado de C-22/23/24
