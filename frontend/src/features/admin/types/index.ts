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
  email?: string | null
  nombre?: string | null
  apellidos?: string | null
  legajo?: string | null
  roles?: RolUsuario[]
  activo: boolean
  tenant_id: string
  created_at: string
}

export interface UsuarioActivarToggle {
  activo: boolean
}

// ─── Auditoría ────────────────────────────────────────────────────────────────

export interface AccionPorDia {
  fecha: string
  total: number
}

export interface InteraccionDocente {
  actor_id: string
  total: number
}

export interface InteraccionMateria {
  actor_id: string
  materia_id: string | null
  total: number
}

export interface PanelMetricas {
  acciones_por_dia: AccionPorDia[]
  por_docente: InteraccionDocente[]
  por_materia: InteraccionMateria[]
}

export interface LogEntry {
  id: string
  tenant_id: string
  actor_id: string
  actor_impersonado_id: string | null
  accion: string
  detalle: Record<string, unknown> | null
  filas_afectadas: number
  ip: string
  user_agent: string
  fecha_hora: string
}

export interface LogPaginado {
  total: number
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
