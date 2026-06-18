// features/coordinacion/services/equiposService.ts
import { api } from '@/shared/services/api'
import type {
  Asignacion,
  AsignacionCreate,
  AsignacionFilter,
  AsignacionMasivaOut,
  AsignacionMasivaPayload,
  AsignacionUpdate,
  ClonarEquipoPayload,
  VigenciaMasivaOut,
  VigenciaMasivaPayload,
} from '../types'

export interface UsuarioSimple {
  id: string
  nombre: string
  apellidos: string | null
  email: string | null
}

export async function getUsuarios(): Promise<UsuarioSimple[]> {
  const { data } = await api.get<UsuarioSimple[]>('/v1/users')
  return data
}

export async function getAsignaciones(filters?: AsignacionFilter): Promise<Asignacion[]> {
  const params: Record<string, string> = {}
  if (filters?.materia_id) params.materia_id = filters.materia_id
  if (filters?.carrera_id) params.carrera_id = filters.carrera_id
  if (filters?.cohorte_id) params.cohorte_id = filters.cohorte_id
  if (filters?.usuario_id) params.usuario_id = filters.usuario_id
  if (filters?.rol) params.rol = filters.rol
  if (filters?.solo_vigentes) params.solo_vigentes = 'true'
  const { data } = await api.get<Asignacion[]>('/v1/equipos/', { params })
  return data
}

export async function createAsignacion(payload: AsignacionCreate): Promise<Asignacion> {
  const { data } = await api.post<Asignacion>('/v1/equipos/', payload)
  return data
}

export async function updateAsignacion(id: string, payload: AsignacionUpdate): Promise<Asignacion> {
  const { data } = await api.put<Asignacion>(`/v1/equipos/${id}`, payload)
  return data
}

export async function deleteAsignacion(id: string): Promise<void> {
  await api.delete(`/v1/equipos/${id}`)
}

export async function getMisAsignaciones(): Promise<Asignacion[]> {
  const { data } = await api.get<Asignacion[]>('/v1/equipos/mis-asignaciones')
  return data
}

export async function asignacionMasiva(payload: AsignacionMasivaPayload): Promise<AsignacionMasivaOut> {
  const { data } = await api.post<AsignacionMasivaOut>('/v1/equipos/asignacion-masiva', payload)
  return data
}

export async function clonarEquipo(payload: ClonarEquipoPayload): Promise<AsignacionMasivaOut> {
  const { data } = await api.post<AsignacionMasivaOut>('/v1/equipos/clonar', payload)
  return data
}

export async function vigenciaMasiva(payload: VigenciaMasivaPayload): Promise<VigenciaMasivaOut> {
  const { data } = await api.put<VigenciaMasivaOut>('/v1/equipos/vigencia-masiva', payload)
  return data
}
