import { api } from '@/shared/services/api'

export const DIAS_SEMANA = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo'] as const
export type DiaSemana = typeof DIAS_SEMANA[number]

export const ESTADOS_GUARDIA = ['Pendiente', 'Realizada', 'Cancelada'] as const
export type EstadoGuardia = typeof ESTADOS_GUARDIA[number]

export interface Guardia {
  id: string
  tenant_id: string
  asignacion_id: string
  materia_id: string
  carrera_id: string
  cohorte_id: string
  dia: string
  horario: string
  estado: string
  comentarios: string | null
  created_at: string
  updated_at: string
}

export interface GuardiaCreate {
  asignacion_id: string
  materia_id: string
  carrera_id: string
  cohorte_id: string
  dia: DiaSemana
  horario: string
  estado?: EstadoGuardia
  comentarios?: string | null
}

export interface GuardiaFilter {
  materia_id?: string
  carrera_id?: string
  cohorte_id?: string
  asignacion_id?: string
  estado?: string
}

export async function getGuardias(filters?: GuardiaFilter): Promise<Guardia[]> {
  const params: Record<string, string> = {}
  if (filters?.materia_id) params.materia_id = filters.materia_id
  if (filters?.carrera_id) params.carrera_id = filters.carrera_id
  if (filters?.cohorte_id) params.cohorte_id = filters.cohorte_id
  if (filters?.asignacion_id) params.asignacion_id = filters.asignacion_id
  if (filters?.estado) params.estado = filters.estado
  const { data } = await api.get<Guardia[]>('/v1/guardias/', { params })
  return data
}

export async function createGuardia(payload: GuardiaCreate): Promise<Guardia> {
  const { data } = await api.post<Guardia>('/v1/guardias/', payload)
  return data
}

export async function exportarGuardias(filters?: GuardiaFilter): Promise<void> {
  const params: Record<string, string> = {}
  if (filters?.materia_id) params.materia_id = filters.materia_id
  if (filters?.carrera_id) params.carrera_id = filters.carrera_id
  if (filters?.cohorte_id) params.cohorte_id = filters.cohorte_id
  if (filters?.asignacion_id) params.asignacion_id = filters.asignacion_id
  if (filters?.estado) params.estado = filters.estado
  const { data } = await api.get('/v1/guardias/exportar', { params, responseType: 'blob' })
  const url = URL.createObjectURL(new Blob([data]))
  const a = document.createElement('a')
  a.href = url
  a.download = 'guardias.csv'
  a.click()
  URL.revokeObjectURL(url)
}
