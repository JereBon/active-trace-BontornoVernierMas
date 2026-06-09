// features/coordinacion/services/avisosService.ts
import { api } from '@/shared/services/api'
import type { Aviso, AvisoCreate } from '../types'

export async function getAvisos(): Promise<Aviso[]> {
  const { data } = await api.get<Aviso[]>('/v1/avisos')
  return data
}

export async function createAviso(payload: AvisoCreate): Promise<Aviso> {
  const { data } = await api.post<Aviso>('/v1/avisos', payload)
  return data
}

export async function updateAviso(id: string, payload: Partial<AvisoCreate>): Promise<Aviso> {
  const { data } = await api.patch<Aviso>(`/v1/avisos/${id}`, payload)
  return data
}

export async function archivarAviso(id: string): Promise<Aviso> {
  const { data } = await api.post<Aviso>(`/v1/avisos/${id}/archivar`)
  return data
}
