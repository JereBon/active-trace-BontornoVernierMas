// features/coordinacion/types/index.ts
// TypeScript types for C-23 frontend-coordinacion — mirrors backend schemas

// ─── Asignaciones (Equipos Docentes) ──────────────────────────────────────────

export interface EquipoDocente {
  id: string
  tenant_id: string
  usuario_id: string
  rol: string
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

export interface EquipoDocenteCreate {
  usuario_id: string
  rol: string
  materia_id?: string | null
  carrera_id?: string | null
  cohorte_id?: string | null
  comisiones?: string[]
  desde: string
  hasta?: string | null
}

export interface EquipoDocenteUpdate {
  rol?: string
  materia_id?: string | null
  desde?: string
  hasta?: string | null
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
  scope?: AvisoScope
  scope_valor?: string | null
  vig_desde: string
  vig_hasta: string
}

// ─── Tareas ───────────────────────────────────────────────────────────────────

export type TareaEstado = 'Pendiente' | 'En_progreso' | 'Resuelta' | 'Cancelada'

export interface Tarea {
  id: string
  titulo: string
  descripcion: string | null
  estado: TareaEstado
  asignado_a: string
  asignado_por: string
  materia_id: string | null
  contexto_id: string | null
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface TareaCreate {
  titulo: string
  descripcion?: string | null
  asignado_a: string
  materia_id?: string | null
  contexto_id?: string | null
}

export interface ComentarioTarea {
  id: string
  tarea_id: string
  autor_id: string
  contenido: string
  created_at: string
  updated_at: string
}

export interface ComentarioTareaCreate {
  contenido: string
}

// ─── Encuentros ───────────────────────────────────────────────────────────────

export interface EncuentroAdmin {
  id: string
  tenant_id: string
  slot_id: string | null
  materia_id: string
  fecha: string
  hora: string
  titulo: string
  estado: string
  meet_url: string | null
  video_url: string | null
  comentario: string | null
  created_at: string
  updated_at: string
}

export interface EncuentroCreate {
  asignacion_id: string
  materia_id: string
  titulo: string
  hora: string
  dia_semana: string
  fecha_inicio: string
  cant_semanas: number
  fecha_unica?: string | null
  meet_url?: string | null
}

export interface EncuentroInstanciaUpdate {
  estado?: string
  meet_url?: string | null
  video_url?: string | null
  comentario?: string | null
}

// ─── Coloquios ────────────────────────────────────────────────────────────────

export type ColoquioEstado = 'Abierta' | 'Cerrada' | 'Cancelada'
export type ColoquioTipo = 'Parcial' | 'TP' | 'Coloquio' | 'Recuperatorio'

export interface ColoquioConvocatoria {
  id: string
  tenant_id: string
  materia_id: string
  cohorte_id: string
  tipo: ColoquioTipo
  instancia: string
  dias_disponibles: number
  cupos_disponibles: number
  estado: ColoquioEstado
  created_at: string
  updated_at: string
}

export interface ColoquioCreate {
  materia_id: string
  cohorte_id: string
  tipo?: ColoquioTipo
  instancia: string
  dias_disponibles: number
  cupos_disponibles: number
}

export interface ColoquioPatch {
  instancia?: string
  dias_disponibles?: number
  cupos_disponibles?: number
  estado?: ColoquioEstado
}
