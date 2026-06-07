// features/admin/types/index.ts
// TypeScript types for C-24 admin feature — mirrors backend schemas

// ─── Estructura Académica ─────────────────────────────────────────────────────

export interface Carrera {
  id: string
  nombre: string
  codigo: string
  activa: boolean
  tenant_id: string
  created_at: string
}

export interface CarreraCreate {
  nombre: string
  codigo: string
}

export interface CarreraUpdate {
  nombre?: string
  codigo?: string
  activa?: boolean
}

export interface Cohorte {
  id: string
  carrera_id: string
  carrera_nombre: string | null
  anio: number
  plan: string | null
  activa: boolean
  tenant_id: string
  created_at: string
}

export interface CohorteCreate {
  carrera_id: string
  anio: number
  plan?: string | null
}

export interface CohorteUpdate {
  anio?: number
  plan?: string | null
  activa?: boolean
}

export interface Materia {
  id: string
  nombre: string
  codigo: string
  categoria_clave: string | null
  activa: boolean
  tenant_id: string
  created_at: string
}

export interface MateriaCreate {
  nombre: string
  codigo: string
  categoria_clave?: string | null
}

export interface MateriaUpdate {
  nombre?: string
  codigo?: string
  categoria_clave?: string | null
  activa?: boolean
}

// ─── Usuarios del Tenant ──────────────────────────────────────────────────────

export type RolUsuario = 'ALUMNO' | 'TUTOR' | 'PROFESOR' | 'COORDINADOR' | 'NEXO' | 'ADMIN' | 'FINANZAS'

export interface Usuario {
  id: string
  email: string
  nombre: string
  apellido: string
  legajo: string | null
  roles: RolUsuario[]
  activo: boolean
  tenant_id: string
  created_at: string
}

export interface UsuarioActivarToggle {
  activo: boolean
}

// ─── Auditoría ────────────────────────────────────────────────────────────────

export interface PanelMetricas {
  total_acciones: number
  acciones_hoy: number
  top_acciones: Array<{ accion: string; cantidad: number }>
  top_actores: Array<{ actor_id: string; nombre: string | null; cantidad: number }>
}

export interface LogEntry {
  id: string
  actor_id: string
  actor_nombre: string | null
  accion: string
  recurso_tipo: string | null
  recurso_id: string | null
  detalle: Record<string, unknown> | null
  ip: string | null
  created_at: string
}

export interface LogPaginado {
  total: number
  offset: number
  limit: number
  items: LogEntry[]
}

export interface LogFiltros {
  fecha_desde?: string
  fecha_hasta?: string
  usuario_id?: string
  accion?: string
  limit?: number
  offset?: number
}
