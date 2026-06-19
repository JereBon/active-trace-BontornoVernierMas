// features/coordinacion/services/encuentrosService.ts
import { api } from '@/shared/services/api'
import type { InstanciaEncuentro, InstanciaUpdate, SlotCreate, SlotWithInstancesOut } from '../types'

export async function getEncuentros(): Promise<InstanciaEncuentro[]> {
  const { data } = await api.get<InstanciaEncuentro[]>('/v1/encuentros/admin')
  return data
}

export async function createSlot(payload: SlotCreate): Promise<SlotWithInstancesOut> {
  const { data } = await api.post<SlotWithInstancesOut>('/v1/encuentros/slots', payload)
  return data
}

export async function updateInstancia(id: string, payload: InstanciaUpdate): Promise<InstanciaEncuentro> {
  const { data } = await api.patch<InstanciaEncuentro>(`/v1/encuentros/${id}`, payload)
  return data
}

export async function exportarHtmlEncuentros(materiaId?: string): Promise<string> {
  const params: Record<string, string> = {}
  if (materiaId) params.materia_id = materiaId
  const { data } = await api.get('/v1/encuentros/html', { params, responseType: 'text' })
  return data
}
