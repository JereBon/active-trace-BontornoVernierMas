// features/coordinacion/services/equiposService.ts
import { api } from '@/shared/services/api'
import type { EquipoDocente, EquipoDocenteCreate, EquipoDocenteUpdate } from '../types'

export async function getEquipos(responsableId?: string): Promise<EquipoDocente[]> {
  const params = responsableId ? { usuario_id: responsableId } : {}
  const { data } = await api.get<EquipoDocente[]>('/v1/equipos/', { params })
  return data
}

export async function createEquipo(payload: EquipoDocenteCreate): Promise<EquipoDocente> {
  const { data } = await api.post<EquipoDocente>('/v1/equipos/', payload)
  return data
}

export async function updateEquipo(id: string, payload: EquipoDocenteUpdate): Promise<EquipoDocente> {
  const { data } = await api.put<EquipoDocente>(`/v1/equipos/${id}`, payload)
  return data
}

export async function deleteEquipo(id: string): Promise<void> {
  await api.delete(`/v1/equipos/${id}`)
}

export async function getMisAsignaciones(): Promise<EquipoDocente[]> {
  const { data } = await api.get<EquipoDocente[]>('/v1/equipos/mis-asignaciones')
  return data
}

export interface ClonarEquipoPayload {
  materia_id: string
  carrera_id: string
  origen_cohorte_id: string
  destino_cohorte_id: string
  desde: string
  hasta?: string | null
}

export async function clonarEquipo(payload: ClonarEquipoPayload): Promise<unknown> {
  const { data } = await api.post('/v1/equipos/clonar', payload)
  return data
}
