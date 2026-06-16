"""core/permisos.py — Permission constants catalogue (C-04: RBAC).

Single source of truth for all permission strings used in the codebase.
Import these constants in routers and tests instead of spelling raw strings.

Format: MODULO_ACCION = "modulo:accion"

These strings MUST match the 'codigo' column values seeded by 0003_rbac.py.
"""

# ── Académico ────────────────────────────────────────────────────────────────
ACADEMICO_VER_PROPIO = "academico:ver_propio"

# ── Evaluaciones (coloquios) ──────────────────────────────────────────────────
EVALUACIONES_RESERVAR = "evaluaciones:reservar"
EVALUACIONES_GESTIONAR = "evaluaciones:gestionar"
EVALUACIONES_RESULTADO = "evaluaciones:resultado"

# ── Avisos ────────────────────────────────────────────────────────────────────
AVISOS_CONFIRMAR = "avisos:confirmar"
AVISOS_PUBLICAR = "avisos:publicar"

# ── Calificaciones ────────────────────────────────────────────────────────────
CALIFICACIONES_IMPORTAR = "calificaciones:importar"
CALIFICACIONES_UMBRAL = "calificaciones:umbral"

# ── Atrasados ─────────────────────────────────────────────────────────────────
ATRASADOS_VER = "atrasados:ver"

# ── Entregas ──────────────────────────────────────────────────────────────────
ENTREGAS_VER_SIN_CORREGIR = "entregas:ver_sin_corregir"

# ── Comunicación ──────────────────────────────────────────────────────────────
COMUNICACION_ENVIAR = "comunicacion:enviar"
COMUNICACION_APROBAR = "comunicacion:aprobar"

# ── Encuentros ────────────────────────────────────────────────────────────────
ENCUENTROS_GESTIONAR = "encuentros:gestionar"

# ── Guardias ──────────────────────────────────────────────────────────────────
GUARDIAS_REGISTRAR = "guardias:registrar"

# ── Tareas ────────────────────────────────────────────────────────────────────
TAREAS_GESTIONAR = "tareas:gestionar"

# ── Equipos ───────────────────────────────────────────────────────────────────
EQUIPOS_ASIGNAR = "equipos:asignar"

# ── Estructura académica ──────────────────────────────────────────────────────
ESTRUCTURA_GESTIONAR = "estructura:gestionar"

# ── Usuarios ──────────────────────────────────────────────────────────────────
USUARIOS_GESTIONAR = "usuarios:gestionar"

# ── Auditoría ─────────────────────────────────────────────────────────────────
AUDITORIA_VER = "auditoria:ver"

# ── Liquidaciones ─────────────────────────────────────────────────────────────
LIQUIDACIONES_OPERAR = "liquidaciones:operar"
LIQUIDACIONES_CERRAR = "liquidaciones:cerrar"

# ── Facturas ──────────────────────────────────────────────────────────────────
FACTURAS_GESTIONAR = "facturas:gestionar"

# ── Tenant ────────────────────────────────────────────────────────────────────
TENANT_CONFIGURAR = "tenant:configurar"

# ── Impersonación ─────────────────────────────────────────────────────────────
IMPERSONACION_USAR = "impersonacion:usar"

# ── Padrón ────────────────────────────────────────────────────────────────────
PADRON_LEER = "padron:leer"
PADRON_CARGAR = "padron:cargar"
PADRON_VACIAR = "padron:vaciar"


# ── Full catalogue (used by tests / seed validation) ─────────────────────────
ALL_PERMISOS: frozenset[str] = frozenset(
    {
        ACADEMICO_VER_PROPIO,
        EVALUACIONES_RESERVAR,
        EVALUACIONES_GESTIONAR,
        EVALUACIONES_RESULTADO,
        AVISOS_CONFIRMAR,
        AVISOS_PUBLICAR,
        CALIFICACIONES_IMPORTAR,
        CALIFICACIONES_UMBRAL,
        ATRASADOS_VER,
        ENTREGAS_VER_SIN_CORREGIR,
        COMUNICACION_ENVIAR,
        COMUNICACION_APROBAR,
        ENCUENTROS_GESTIONAR,
        GUARDIAS_REGISTRAR,
        TAREAS_GESTIONAR,
        EQUIPOS_ASIGNAR,
        ESTRUCTURA_GESTIONAR,
        USUARIOS_GESTIONAR,
        AUDITORIA_VER,
        LIQUIDACIONES_OPERAR,
        LIQUIDACIONES_CERRAR,
        FACTURAS_GESTIONAR,
        TENANT_CONFIGURAR,
        IMPERSONACION_USAR,
        PADRON_LEER,
        PADRON_CARGAR,
        PADRON_VACIAR,
    }
)
