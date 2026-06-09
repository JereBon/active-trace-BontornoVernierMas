// features/comision/types/index.ts
// TypeScript types mirroring backend schemas for C-22 frontend-academico-docente

// ─── Calificaciones ────────────────────────────────────────────────────────────

export interface AlumnoPreviewItem {
  email: string
  notas: Record<string, unknown>
}

export interface CalificacionPreviewResponse {
  actividades_numericas: string[]
  actividades_textuales: string[]
  alumnos_preview: AlumnoPreviewItem[]
}

export interface ImportarResponse {
  calificaciones_importadas: number
  mensaje: string
}

export interface UmbralRequest {
  asignacion_id: string
  umbral_pct: number
  valores_aprobatorios: string[]
}

export interface UmbralResponse {
  id: string
  asignacion_id: string
  materia_id: string
  umbral_pct: number
  valores_aprobatorios: string[]
}

// ─── Análisis ─────────────────────────────────────────────────────────────────

export interface AtrasadoItem {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  comision: string | null
  regional: string | null
  actividades_faltantes: string[]
  actividades_no_aprobadas: string[]
}

export interface RankingItem {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  comision: string | null
  cant_aprobadas: number
}

export interface NotaFinal {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  comision: string | null
  nota_final: number | null
}

export interface ReporteMateria {
  materia_id: string
  total_alumnos: number
  total_actividades: number
  alumnos_con_aprobada: number
  alumnos_atrasados: number
  porcentaje_aprobacion: number
}

export interface SinCorregirItem {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  comision: string | null
  actividad: string
  importado_at: string
}

export interface MonitorItem {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  comision: string | null
  regional: string | null
  materia_id: string
  cant_actividades: number
  cant_aprobadas: number
  cant_no_aprobadas: number
  cant_faltantes: number
  es_atrasado: boolean
}

// ─── Comunicaciones ───────────────────────────────────────────────────────────

export type LoteEstado = 'Pendiente' | 'Enviado' | 'Fallido' | 'Cancelado'

export interface ComunicacionOut {
  id: string
  lote_id: string
  destinatario: string
  asunto: string
  estado: LoteEstado
  aprobado: boolean
  enviado_at: string | null
  created_at: string
}

export interface LoteStatus {
  lote_id: string
  total: number
  pendientes: number
  enviados: number
  errores: number
  cancelados: number
  mensajes: ComunicacionOut[]
}

export interface PreviewComunicacion {
  asunto: string
  cuerpo: string
}

export interface MonitorParams {
  materia_id?: string
  comision?: string
  regional?: string
  alumno_nombre?: string
  solo_atrasados?: boolean
  limit?: number
  offset?: number
}
