// features/coordinacion/services/fechasService.ts
import { api } from '@/shared/services/api'

export type FechaTipo = 'PARCIAL' | 'TP' | 'COLOQUIO' | 'RECUPERATORIO'

export interface FechaCreate {
  materia_id: string
  cohorte_id: string
  tipo: FechaTipo
  numero: number
  periodo: string
  fecha: string // YYYY-MM-DD
  titulo: string
}

export interface FechaOut extends FechaCreate {
  id: string
  tenant_id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export async function getFechas(materiaId?: string): Promise<FechaOut[]> {
  const params = materiaId ? { materia_id: materiaId } : {}
  const { data } = await api.get<FechaOut[]>('/v1/fechas-academicas', { params })
  return data
}

export async function createFecha(payload: FechaCreate): Promise<FechaOut> {
  const { data } = await api.post<FechaOut>('/v1/fechas-academicas', payload)
  return data
}

export async function deleteFecha(id: string): Promise<void> {
  await api.delete(`/v1/fechas-academicas/${id}`)
}
