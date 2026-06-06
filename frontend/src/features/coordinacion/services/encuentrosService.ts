// features/coordinacion/services/encuentrosService.ts
import { api } from '@/shared/services/api'
import type { EncuentroAdmin, EncuentroCreate } from '../types'

export async function getEncuentros(): Promise<EncuentroAdmin[]> {
  const { data } = await api.get<EncuentroAdmin[]>('/v1/encuentros')
  return data
}

export async function createEncuentro(payload: EncuentroCreate): Promise<EncuentroAdmin> {
  const { data } = await api.post<EncuentroAdmin>('/v1/encuentros', payload)
  return data
}
