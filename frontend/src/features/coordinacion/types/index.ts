// features/coordinacion/types/index.ts
// TypeScript types for C-23 frontend-coordinacion — mirrors backend schemas

// ─── Equipos Docentes ──────────────────────────────────────────────────────────

export interface DocenteResumen {
  id: string
  nombre: string
  email: string
  rol: string
}

export interface EquipoDocente {
  id: string
  nombre: string
  descripcion: string | null
  vigencia_desde: string | null
  vigencia_hasta: string | null
  integrantes: DocenteResumen[]
  tenant_id: string
  created_at: string
}

export interface EquipoDocenteCreate {
  nombre: string
  descripcion?: string | null
  vigencia_desde?: string | null
  vigencia_hasta?: string | null
}

export interface EquipoDocenteUpdate {
  nombre?: string
  descripcion?: string | null
  vigencia_desde?: string | null
  vigencia_hasta?: string | null
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

export type EncuentroTipo = 'presencial' | 'virtual' | 'hibrido'
export type EncuentroEstado = 'programado' | 'realizado' | 'cancelado'

export interface EncuentroAdmin {
  id: string
  fecha: string
  tipo: EncuentroTipo
  cupo_maximo: number | null
  estado: EncuentroEstado
  descripcion: string | null
  tenant_id: string
  created_at: string
}

export interface EncuentroCreate {
  fecha: string
  tipo: EncuentroTipo
  cupo_maximo?: number | null
  descripcion?: string | null
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
