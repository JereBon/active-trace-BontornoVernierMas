// features/coordinacion/services/encuentrosService.ts
import { api } from '@/shared/services/api'
import type { EncuentroAdmin, EncuentroCreate, EncuentroInstanciaUpdate } from '../types'

export async function getEncuentros(): Promise<EncuentroAdmin[]> {
  const { data } = await api.get<EncuentroAdmin[]>('/v1/encuentros/admin')
  return data
}

export async function createEncuentro(payload: EncuentroCreate): Promise<{ slot: unknown; instancias: EncuentroAdmin[] }> {
  const { data } = await api.post<{ slot: unknown; instancias: EncuentroAdmin[] }>('/v1/encuentros/slots', payload)
  return data
}

export async function updateInstancia(id: string, payload: EncuentroInstanciaUpdate): Promise<EncuentroAdmin> {
  const { data } = await api.patch<EncuentroAdmin>(`/v1/encuentros/${id}`, payload)
  return data
}
