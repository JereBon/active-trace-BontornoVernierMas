## Context

Los changes C-22, C-23 y C-24 se implementaron sin una auditoría final de consistencia. Al revisar contra la documentación y las reglas duras del proyecto, se encontraron múltiples desviaciones: el AuthGuard no verificaba roles (solo autenticación), `deleteCarrera` usaba HTTP DELETE violando la regla de soft-delete, `useAuth.ts` nunca llamaba `getMeApi()` dejando `full_name` y `email` vacíos, los Zod schemas no usaban `.strict()`, el formulario de cohorte pedía UUID manual, y features backend completas (crear factura, calcular liquidaciones) no tenían UI.

Este change es puramente correctivo — no introduce nuevas funcionalidades, solo alinea el frontend con las reglas del proyecto y la documentación.

## Goals / Non-Goals

**Goals:**
- Proteger rutas del frontend por rol (fail-closed)
- Reemplazar hard-delete por soft-delete en carreras
- Mostrar datos reales del usuario en Navbar (full_name, email)
- Actualizar CHANGES.md con estado real de C-22/23/24
- Agregar `.strict()` a todos los Zod schemas de estructura académica
- Reemplazar input UUID de carrera en cohorte por select de carreras activas
- Mostrar nombre del usuario en panel de auditoría en vez de UUID crudo
- Agregar UI para crear facturas
- Agregar botón para calcular liquidaciones

**Non-Goals:**
- No se modifican endpoints del backend
- No se agregan nuevas features más allá de las UIs faltantes
- No se modifican tests existentes (solo se asegura que pasen)

## Decisions

1. **AuthGuard con `requiredRoles`**: Se agrega prop opcional al guard existente en vez de crear un nuevo componente `RoleGuard`. Esto mantiene la interfaz simple y evita duplicación. Si no hay roles requeridos, se comporta como antes (solo auth).

2. **Soft-delete como PATCH**: `deleteCarrera` ahora llama `api.patch()` con `{ activa: false }` en vez de `api.delete()`. Coincide con el endpoint del backend que ya soporta PATCH.

3. **getMeApi en flujo de auth**: Se llama `getMeApi()` después de login y después del silent refresh (en vez de solo decodificar el JWT). El JWT solo tiene sub, tenant_id y roles — el perfil completo (full_name, email) requiere una llamada adicional.

4. **Select de carreras en cohorte**: Se usa `useCarreras()` para poblar un `<select>` filtrando solo carreras activas. El valor del select es el UUID de la carrera, manteniendo compatibilidad con el schema Zod.

5. **actor_id como nombre**: Se usa `useUsuarios()` para construir un `Map<id, nombre>` y se resuelve en las celdas de la tabla de auditoría y en los top docentes. Si el usuario no está en el map (ej: fue borrado), se muestra el UUID como fallback.

## Risks / Trade-offs

- **Rendimiento en PanelAuditoria**: `useUsuarios()` agrega una query adicional. Para paneles con muchos datos, considerar cachear el map de usuarios. Por ahora es aceptable porque se usa el hook de TanStack Query que ya cachea.
- **AuthGuard anidado**: Las rutas con role checking quedan dentro del AuthGuard principal que ya verifica autenticación. Hay doble verificación, pero es intencional: el outer guard maneja auth, el inner guard maneja roles.
