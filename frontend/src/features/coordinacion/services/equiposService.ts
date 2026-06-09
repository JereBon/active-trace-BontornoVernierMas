// features/coordinacion/services/equiposService.ts
import { api } from '@/shared/services/api'
import type { EquipoDocente, EquipoDocenteCreate, EquipoDocenteUpdate } from '../types'

export interface Asignacion {
  id: string
  materia_id: string
  rol: string
  desde: string
  hasta: string | null
}

export async function getMisAsignaciones(): Promise<Asignacion[]> {
  const { data } = await api.get<Asignacion[]>('/v1/equipos/mis-asignaciones')
  return data
}

export async function getEquipos(): Promise<EquipoDocente[]> {
  const { data } = await api.get<EquipoDocente[]>('/v1/equipos/')
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

export async function clonarEquipo(origen_cohorte_id: string, destino_cohorte_id: string): Promise<EquipoDocente[]> {
  const { data } = await api.post<{ creadas: EquipoDocente[] }>('/v1/equipos/clonar', { origen_cohorte_id, destino_cohorte_id })
  return data.creadas
}
