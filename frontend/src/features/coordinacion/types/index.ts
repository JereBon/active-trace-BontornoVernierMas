// features/coordinacion/types/index.ts
// TypeScript types for coordinacion — mirrors backend schemas (extra='forbid')

// ─── Equipos Docentes (Asignaciones) ──────────────────────────────────────────

export const ROLES_ASIGNACION = ['ALUMNO', 'TUTOR', 'PROFESOR', 'COORDINADOR', 'NEXO', 'ADMIN', 'FINANZAS'] as const
export type RolAsignacion = typeof ROLES_ASIGNACION[number]

export interface Asignacion {
  id: string
  tenant_id: string
  usuario_id: string
  rol: RolAsignacion
  materia_id: string | null
  carrera_id: string | null
  cohorte_id: string | null
  comisiones: string[]
  responsable_id: string | null
  desde: string
  hasta: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface AsignacionCreate {
  usuario_id: string
  rol: RolAsignacion
  desde: string
  hasta?: string | null
  materia_id?: string | null
  carrera_id?: string | null
  cohorte_id?: string | null
  comisiones?: string[]
  responsable_id?: string | null
}

export interface AsignacionUpdate {
  rol?: RolAsignacion
  desde?: string
  hasta?: string | null
  materia_id?: string | null
  carrera_id?: string | null
  cohorte_id?: string | null
  comisiones?: string[]
  responsable_id?: string | null
}

export interface AsignacionFilter {
  materia_id?: string | null
  carrera_id?: string | null
  cohorte_id?: string | null
  usuario_id?: string | null
  rol?: string | null
  solo_vigentes?: boolean
}

export interface AsignacionMasivaPayload {
  usuario_ids: string[]
  rol: RolAsignacion
  desde: string
  hasta?: string | null
  materia_id?: string | null
  carrera_id?: string | null
  cohorte_id?: string | null
  comisiones?: string[]
  responsable_id?: string | null
}

export interface ClonarEquipoPayload {
  materia_id: string
  carrera_id: string
  origen_cohorte_id: string
  destino_cohorte_id: string
  desde: string
  hasta?: string | null
}

export interface VigenciaMasivaPayload {
  materia_id: string
  carrera_id: string
  cohorte_id: string
  desde: string
  hasta?: string | null
}

export interface AsignacionMasivaOut {
  creadas: Asignacion[]
  omitidos: string[]
}

export interface VigenciaMasivaOut {
  filas_afectadas: number
}

// ─── Avisos ───────────────────────────────────────────────────────────────────

export type AvisoScope = 'TODOS' | 'ROL' | 'USUARIO'

export interface Aviso {
  id: string
  tenant_id: string
  titulo: string
  cuerpo: string
  scope: AvisoScope
  scope_valor: string | null
  vig_desde: string
  vig_hasta: string
  activo: boolean
  publicado_por: string
  created_at: string
  updated_at: string
}

export interface AvisoCreate {
  titulo: string
  cuerpo: string
  scope: AvisoScope
  scope_valor?: string | null
  vig_desde: string
  vig_hasta: string
}

// ─── Tareas ───────────────────────────────────────────────────────────────────

export type TareaEstado = 'pendiente' | 'en_progreso' | 'completada'
export type TareaPrioridad = 'baja' | 'media' | 'alta'

export interface Tarea {
  id: string
  titulo: string
  descripcion: string | null
  estado: TareaEstado
  prioridad: TareaPrioridad
  asignado_a: string | null
  asignado_nombre: string | null
  asignado_por: string | null
  creado_por: string
  materia_id: string | null
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface TareaCreate {
  titulo: string
  descripcion?: string | null
  prioridad: TareaPrioridad
  asignado_a?: string | null
  materia_id?: string | null
  contexto_id?: string | null
}

export interface TareaUpdate {
  titulo?: string
  descripcion?: string | null
  estado?: TareaEstado
  prioridad?: TareaPrioridad
  asignado_a?: string | null
  materia_id?: string | null
}

export interface ComentarioTarea {
  id: string
  tarea_id: string
  autor_id: string
  autor_nombre: string
  contenido: string
  created_at: string
}

export interface ComentarioTareaCreate {
  contenido: string
}

// ─── Encuentros (backend: SlotCreate / InstanciaOut) ──────────────────────────

export type DiaSemana = 'Lunes' | 'Martes' | 'Miercoles' | 'Jueves' | 'Viernes' | 'Sabado' | 'Domingo'
export type EstadoEncuentro = 'Programado' | 'Realizado' | 'Cancelado'

export interface SlotCreate {
  asignacion_id: string
  materia_id: string
  titulo: string
  hora: string
  dia_semana: DiaSemana
  fecha_inicio: string
  cant_semanas: number
  fecha_unica?: string | null
  meet_url?: string | null
  vig_desde?: string | null
  vig_hasta?: string | null
}

export interface InstanciaEncuentro {
  id: string
  tenant_id: string
  slot_id: string | null
  materia_id: string
  fecha: string
  hora: string
  titulo: string
  estado: EstadoEncuentro
  meet_url: string | null
  video_url: string | null
  comentario: string | null
  created_at: string
  updated_at: string
}

export interface InstanciaUpdate {
  estado?: EstadoEncuentro
  meet_url?: string | null
  video_url?: string | null
  comentario?: string | null
}

export interface SlotOut {
  id: string
  tenant_id: string
  asignacion_id: string
  materia_id: string
  titulo: string
  hora: string
  dia_semana: string
  fecha_inicio: string
  cant_semanas: number
  fecha_unica: string | null
  meet_url: string | null
  vig_desde: string | null
  vig_hasta: string | null
  created_at: string
  updated_at: string
}

export interface SlotWithInstancesOut {
  slot: SlotOut
  instancias: InstanciaEncuentro[]
}

// ─── Coloquios (backend: EvaluacionCreate / EvaluacionOut / Metricas) ─────────

export type TipoEvaluacion = 'Parcial' | 'TP' | 'Coloquio' | 'Recuperatorio'
export type EstadoEvaluacion = 'Abierta' | 'Cerrada' | 'Cancelada'

export interface EvaluacionCreate {
  materia_id: string
  cohorte_id: string
  tipo: TipoEvaluacion
  instancia: string
  dias_disponibles: number
  cupos_disponibles: number
}

export interface EvaluacionOut {
  id: string
  tenant_id: string
  materia_id: string
  cohorte_id: string
  tipo: string
  instancia: string
  dias_disponibles: number
  cupos_disponibles: number
  estado: string
  created_at: string
  updated_at: string
}

export interface EvaluacionMetricas {
  total_convocatorias: number
  total_reservas_activas: number
  total_resultados: number
  total_cupos_libres: number
}

// ─── Cuatrimestre (Asistente de Configuración) ────────────────────────────────

export interface AsignacionCuatrimestre {
  materia_id: string
  usuario_id: string
  rol: RolAsignacion
  desde: string
  hasta: string | null
}
