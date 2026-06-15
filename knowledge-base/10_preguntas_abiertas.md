# 10 — Preguntas Abiertas y Decisiones de Producto Pendientes

> **Propósito**: registrar las decisiones de diseño de producto que aún no están cerradas, ordenadas por impacto sobre el modelo de dominio. Cada ítem es una pregunta genuina que el equipo de producto debe resolver antes de (o durante) la implementación. Las decisiones ya cerradas aparecen en los archivos correspondientes de la KB y en [`docs/ARQUITECTURA.md`](../docs/ARQUITECTURA.md); no se repiten acá. Este archivo es un tablero vivo: cuando una pregunta se cierra, se documenta la resolución en el archivo temático correspondiente y se retira de acá.

---

## Prioridad ALTA — bloqueantes para el modelo de dominio

### ~~PA-01~~ — CERRADA

**Resolución** (2026-06-14):
- Se usa **una sola entidad `Materia`** (del plan de estudios: `codigo`, `nombre`, `categoria_clave`). No existe `InstanciaDictado` como entidad separada.
- La relación materia × cohorte × docente la concentra **`Asignacion`** (`materia_id`, `cohorte_id`, `usuario_id`, `rol`, `comisiones[]`). Cada asignación indica qué comisiones del cuatrimestre cubre ese docente para esa materia.
- Las calificaciones (`Calificacion`) referencian directamente la materia (`materia_id`) más el alumno y la actividad. El campo `comisiones` en `Asignacion` es texto libre (ej. `["C1", "C2"]`) — no hay entidad `Comision` con FK.
- El "dictado" a efectos del LMS (Moodle) es un detalle de integración, no del modelo de dominio.
- Documentado en: `04_modelo_de_datos.md` §E3 (Materia), §E7 (Asignacion), §E5 (Calificacion).

---

### ~~PA-07~~ — CERRADA

**Resolución** (2026-06-14):
- **Una cohorte pertenece a exactamente una carrera** (`Cohorte.carrera_id FK` → `Carrera`). La cardinalidad es N:1. No existen cohortes transversales entre carreras.
- Un alumno puede tener asignaciones en múltiples cohortes (de distintas carreras), pero cada cohorte es exclusiva de su carrera.
- `Cohorte` define el ciclo lectivo (`vig_desde`, `vig_hasta`, `anio`) dentro de una carrera. El plan de estudios vigente se infiere de la carrera.
- Documentado en: `04_modelo_de_datos.md` §E2 (Cohorte → carrera_id FK RESTRICT).

---

### ~~PA-22~~ — CERRADA

**Resolución** (2026-06-07):
- Las claves de grupo son **texto libre configurable por tenant** (FINANZAS/ADMIN). No hay catálogo fijo en el sistema.
- El mapeo materia→clave vive como **campo `categoria_clave: str | None` en la entidad `Materia`**. El ADMIN asigna la clave desde el ABM de materias. Sin tabla separada.
- Una materia sin `categoria_clave` (NULL) **no genera Plus** para el docente — solo contribuye al Base. No bloquea la liquidación.
- Documentado en: `E18 SalarioPlus` (`04_modelo_de_datos.md`), campo `categoria_clave` en `E3 Materia`.

---

### ~~PA-23~~ — CERRADA

**Resolución** (2026-06-07):
- **Acumulación lineal sin tope**: si un docente tiene N comisiones de materias con la misma clave, acumula `N × Plus(clave, rol)`.
- La lógica es uniforme para todos los roles (TUTOR, PROFESOR, NEXO, COORDINADOR).
- Fórmula confirmada por RN-33 y RN-34: `Total = Base(rol) + Σ(Plus(clave, rol) × N_comisiones_por_clave)`.
- Documentado en: RN-33, RN-34 (`05_reglas_de_negocio.md`).

---

### PA-25 — ¿Cuál es la semántica precisa del rol NEXO?

El rol NEXO existe en el dominio, tiene tratamiento contable propio y aparece en el catálogo de roles, pero su función operativa no está completamente especificada.

**Preguntas abiertas**:

- ¿Un NEXO está asociado a una regional, a un programa, a un grupo de docentes, o a un grupo de alumnos?
- ¿Tiene acceso a datos de alumnos? ¿A qué granularidad?
- ¿Puede asignar o reasignar docentes a comisiones?
- ¿Su función es principalmente de enlace administrativo o también pedagógico?
- ¿Un usuario puede ser NEXO y COORDINADOR al mismo tiempo?

**Impacto**: define qué permisos incluir en el rol NEXO dentro de la matriz de autorización ([03_actores_y_roles.md](03_actores_y_roles.md)).

---

## Prioridad MEDIA — refinamiento del modelo

### PA-05 — ¿Cómo y desde dónde se crea una guardia?

El módulo de guardias muestra el listado de guardias registradas por docente, pero el flujo de creación no está especificado.

**Preguntas abiertas**:

- ¿Las guardias se crean desde el módulo de encuentros, desde un formulario dedicado, o ambos?
- ¿Quién puede crear una guardia: solo el docente que la cubre, o también el COORDINADOR en su nombre?
- ¿Requiere aprobación posterior?

---

### ~~PA-08~~ — CERRADA

**Resolución** (2026-06-14):
- Estados implementados: **`Pendiente → En_progreso → Resuelta | Cancelada`** (cuatro estados finales). Almacenados como `String` en lugar de PG ENUM para flexibilidad DDL.
- Transiciones validadas en `TareaService`: no todos los estados son alcanzables desde cualquier origen (estado máquina básico).
- Cambio de estado vía `PATCH /v1/tareas/{id}/estado` con `guard tareas:gestionar`. Delegación vía `POST /v1/tareas/{id}/delegar`.
- No hay notificaciones automáticas de estado en esta versión (fuera de scope MVP).
- Documentado en: `04_modelo_de_datos.md` §E12 (Tarea), `backend/app/models/tarea.py`.

---

### PA-09 — ¿Qué permite la funcionalidad de comunicación por grupos en el módulo de equipos?

Dentro del módulo de equipos docentes existe una funcionalidad de comunicación grupal cuyo alcance no está especificado.

**Preguntas abiertas**:

- ¿Es para enviar mensajes masivos al equipo docente de una comisión?
- ¿O es comunicación entre pares (docentes entre sí)?
- ¿Requiere aprobación previa como las comunicaciones hacia alumnos?

---

### PA-11 — ¿Qué es el "criterio de clasificación" en el monitor general?

El monitor general permite configurar un criterio de clasificación mediante un modal.

**Preguntas abiertas**:

- ¿Qué criterios se pueden configurar? (ej.: por porcentaje de avance, por cantidad de entregas, por calificación promedio)
- ¿La configuración es personal (por usuario) o global (por tenant)?
- ¿Afecta qué alumnos se consideran "atrasados" o es solo una vista?

---

### PA-12 — ¿Qué incluye la vista administrativa de encuentros?

El módulo de encuentros tiene una vista con permisos ampliados respecto a la vista docente estándar.

**Preguntas abiertas**:

- ¿Permite ver y editar los encuentros de todos los docentes de una comisión o de todo el tenant?
- ¿Permite crear encuentros en nombre de otro docente?
- ¿Tiene capacidad de aprobación o solo de consulta?

---

### PA-13 — ¿Qué es el contexto de agrupación de tareas?

El módulo de tareas permite filtrar por un contexto de agrupación cuya semántica no está definida.

**Preguntas abiertas**:

- ¿El contexto de agrupación es una cohorte, una materia, un equipo docente, o algún otro concepto?
- ¿Una tarea puede pertenecer a más de un contexto?

---

### ~~PA-14~~ — CERRADA

**Resolución** (2026-06-14):
- El alumno reserva **desde dentro del sistema** (SPA): `POST /v1/coloquios/{id}/reservas` con permiso `evaluaciones:reservar` (rol ALUMNO).
- El endpoint verifica cupo disponible; si no hay cupo, devuelve 409. Sin restricción de intentos en MVP.
- Cancelación: `DELETE /v1/coloquios/{coloquio_id}/reservas/{reserva_id}` (solo el propio alumno puede cancelar la suya).
- Documentado en: `04_modelo_de_datos.md` §E14 (ReservaEvaluacion), `backend/app/api/v1/routers/coloquios.py`.

---

### PA-15 — ¿El módulo de corrección automática está integrado con las calificaciones?

El sistema contempla la posibilidad de integrar un módulo de corrección automática de actividades.

**Preguntas abiertas**:

- ¿Las calificaciones generadas por el corrector automático se importan al sistema directamente o requieren revisión y aprobación docente?
- ¿El corrector opera sobre entregas ya subidas al sistema o sobre entregas del LMS (Moodle)?
- ¿Cómo se audita una calificación generada automáticamente vs. una ingresada manualmente?

---

### ~~PA-24~~ — CERRADA

**Resolución** (2026-06-14):
- Las facturas son **globales por docente × período**: `Factura(usuario_id, periodo, monto, concepto, estado)`. No hay `comision_id` en el modelo.
- El campo `concepto` es texto libre (descripción del trabajo); `periodo` es `AAAA-MM`, igual que en `Liquidacion`.
- Conciliación: los docentes con `facturador=True` se marcan `excluido_por_factura=True` en la liquidación y quedan fuera del cálculo general. El monto declarado en la factura no es validado automáticamente contra el total liquidado (responsabilidad de FINANZAS).
- Documentado en: `04_modelo_de_datos.md` §E20 (Factura), `backend/app/models/factura.py`.

---

## Prioridad BAJA — pulido y definición de detalles

### PA-16 — ¿Cuáles son los niveles de severidad de los avisos y qué efecto tienen?

**Preguntas abiertas**:

- ¿Los valores de severidad son un enumerado fijo (`info`, `advertencia`, `error`) o es configurable?
- ¿La severidad afecta el comportamiento del sistema (ej.: un aviso de error bloquea al alumno hasta que lo confirme)?
- ¿Hay notificaciones adicionales disparadas por severidad?

---

### PA-17 — ¿El tipo de facturación del docente afecta el cálculo de liquidación?

Algunos docentes pueden emitir comprobantes fiscales (ej.: monotributistas), lo cual puede tener implicancias en el cálculo.

**Preguntas abiertas**:

- ¿El tipo de facturación modifica algún concepto del cálculo (ej.: agrega retenciones, modifica la base)?
- ¿O es solo un atributo informativo para el módulo de FINANZAS sin impacto en la fórmula?

---

### PA-18 — ¿El CUIL del docente se calcula automáticamente o se carga manualmente?

**Preguntas abiertas**:

- ¿El sistema calcula el CUIL a partir del DNI aplicando la regla estándar (`prefijo-DNI-dígito verificador`)?
- ¿O el CUIL es un campo de carga manual sin validación automática?
- Si se calcula, ¿qué pasa cuando el CUIL real difiere del calculado (ej.: personas con CUIL de tipo empresa)?

---

### PA-19 — ¿Qué pasa con las asignaciones vigentes cuando se desactiva un docente?

**Preguntas abiertas**:

- ¿Las asignaciones vigentes se cierran automáticamente (se les pone fecha de fin) al desactivar el usuario?
- ¿O quedan en estado inconsistente hasta que el ADMIN las gestione manualmente?
- ¿El sistema emite una alerta al COORDINADOR cuando uno de sus docentes es desactivado?

---

## Decisiones ya cerradas (referencia)

Las siguientes preguntas que existían en versiones anteriores de este documento ya fueron resueltas y su resolución está documentada en los archivos correspondientes:

| Código original | Resolución | Dónde está documentado |
|-----------------|-----------|------------------------|
| PA-02 | El rol TUTOR existe formalmente en el catálogo; ver descripción de capacidades | [03_actores_y_roles.md](03_actores_y_roles.md) |
| PA-04 | Login por email + contraseña; 2FA opcional (TOTP); recuperación por token de un solo uso; alta solo administrativa en MVP | [07_flujos_principales.md](07_flujos_principales.md), [`docs/ARQUITECTURA.md` §5.1](../docs/ARQUITECTURA.md) |
| PA-06 | Fórmula de liquidación: Base (por rol) + Plus (por clave × rol); ver RN-31 a RN-38 | [05_reglas_de_negocio.md](05_reglas_de_negocio.md) |
| PA-21 | Impersonación via parámetro de petición: eliminada. La impersonación legítima requiere permiso explícito, sesión diferenciada y auditoría completa | [03_actores_y_roles.md §4](03_actores_y_roles.md), [`docs/ARQUITECTURA.md`](../docs/ARQUITECTURA.md) |
| PA-22 | Claves de grupo texto libre por tenant; campo `categoria_clave: str \| None` en `Materia`; NULL → no genera Plus, no bloquea | `04_modelo_de_datos.md` §E18, §E3 |
| PA-23 | Acumulación lineal sin tope: N comisiones × Plus(clave, rol). Uniforme para todos los roles | `05_reglas_de_negocio.md` RN-33, RN-34 |

---

## Cómo cerrar estas preguntas

Para resolver las preguntas pendientes se recomienda:

1. **Una sesión de trabajo con el responsable de producto** — cubre las preguntas de dominio (PA-01, PA-22, PA-23, PA-25 son prioritarias).
2. **Revisión del modelo de datos con el equipo técnico** — para validar las entidades y relaciones de [04_modelo_de_datos.md](04_modelo_de_datos.md).
3. **Sesión de refinamiento con FINANZAS** — para cerrar PA-17, PA-18, PA-24 que afectan el módulo de liquidaciones.
4. **Cuando se cierre una pregunta**: documentar la resolución en el archivo temático correspondiente y moverla a la tabla de "Decisiones ya cerradas" de este archivo.
