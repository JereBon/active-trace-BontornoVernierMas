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

export type AvisoScope = 'todos' | 'coordinadores' | 'profesores' | 'alumnos'
export type AvisoSeveridad = 'info' | 'advertencia' | 'critico'

export interface Aviso {
  id: string
  titulo: string
  cuerpo: string
  scope: AvisoScope
  severidad: AvisoSeveridad
  vigencia_hasta: string | null
  requiere_ack: boolean
  archivado: boolean
  created_at: string
  tenant_id: string
}

export interface AvisoCreate {
  titulo: string
  cuerpo: string
  scope: AvisoScope
  severidad: AvisoSeveridad
  vigencia_hasta?: string | null
  requiere_ack: boolean
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
  creado_por: string
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface TareaCreate {
  titulo: string
  descripcion?: string | null
  prioridad: TareaPrioridad
  asignado_a?: string | null
}

export interface TareaUpdate {
  titulo?: string
  descripcion?: string | null
  estado?: TareaEstado
  prioridad?: TareaPrioridad
  asignado_a?: string | null
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

// ─── Coloquios ────────────────────────────────────────────────────────────────

export type ColoquioEstado = 'abierta' | 'cerrada' | 'cancelada'

export interface ColoquioConvocatoria {
  id: string
  materia_id: string
  materia_nombre: string | null
  fecha: string
  descripcion: string | null
  estado: ColoquioEstado
  tenant_id: string
  created_at: string
}

export interface ColoquioCreate {
  materia_id: string
  fecha: string
  descripcion?: string | null
}
