// features/coordinacion/services/equiposService.ts
import { api } from '@/shared/services/api'
import type { EquipoDocente, EquipoDocenteCreate, EquipoDocenteUpdate } from '../types'

export async function getEquipos(): Promise<EquipoDocente[]> {
  const { data } = await api.get<EquipoDocente[]>('/v1/equipos-docentes')
  return data
}

export async function createEquipo(payload: EquipoDocenteCreate): Promise<EquipoDocente> {
  const { data } = await api.post<EquipoDocente>('/v1/equipos-docentes', payload)
  return data
}

export async function updateEquipo(id: string, payload: EquipoDocenteUpdate): Promise<EquipoDocente> {
  const { data } = await api.patch<EquipoDocente>(`/v1/equipos-docentes/${id}`, payload)
  return data
}

export async function deleteEquipo(id: string): Promise<void> {
  await api.delete(`/v1/equipos-docentes/${id}`)
}

export async function clonarEquipo(id: string): Promise<EquipoDocente> {
  const { data } = await api.post<EquipoDocente>(`/v1/equipos-docentes/${id}/clonar`)
  return data
}
