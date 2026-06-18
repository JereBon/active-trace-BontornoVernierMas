## 1. Role Guard

- [x] 1.1 Agregar prop `requiredRoles` a AuthGuard con redirect a /dashboard
- [x] 1.2 Proteger rutas en App.tsx por rol (ADMIN, FINANZAS, COORDINADOR, PROFESOR/TUTOR)

## 2. Soft-delete en Carreras

- [x] 2.1 Cambiar deleteCarrera de DELETE a PATCH { activa: false }

## 3. User Profile Real en Navbar

- [x] 3.1 Importar getMeApi en useAuth.ts
- [x] 3.2 Llamar getMeApi() tras login exitoso
- [x] 3.3 Llamar getMeApi() tras silent refresh

## 4. Documentación

- [x] 4.1 Marcar C-22/23/24 como [x] en CHANGES.md

## 5. Zod .strict() en Schemas

- [x] 5.1 Agregar .strict() a carreraSchema, cohorteSchema y materiaSchema

## 6. Cohorte Form con Select

- [x] 6.1 Reemplazar input UUID por <select> de carreras activas con useCarreras()

## 7. Auditoría: actor_id como Nombre

- [x] 7.1 Integrar useUsuarios() en PanelAuditoria para resolver UUID a nombre
- [x] 7.2 Mostrar nombre en tabla de log y top docentes

## 8. Factura Create UI

- [x] 8.1 Agregar botón "+ Nueva factura" en TablaFacturas
- [x] 8.2 Implementar modal con formulario de creación
- [x] 8.3 Conectar submit a useCreateFactura()

## 9. Calcular Liquidaciones UI

- [x] 9.1 Agregar botón "Calcular liquidaciones" en VistaPeriodo (visible solo sin datos)
- [x] 9.2 Conectar click a useCalcularLiquidaciones()

## 10. Verificación

- [x] 10.1 Correr test suite completa (74 tests, 20 archivos)
- [x] 10.2 Verificar type-check: tsc --noEmit
