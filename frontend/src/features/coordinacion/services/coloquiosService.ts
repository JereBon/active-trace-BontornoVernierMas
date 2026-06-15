// features/coordinacion/services/coloquiosService.ts
import { api } from '@/shared/services/api'
import type { ColoquioConvocatoria, ColoquioCreate, ColoquioPatch } from '../types'

export async function getColoquios(): Promise<ColoquioConvocatoria[]> {
  const { data } = await api.get<ColoquioConvocatoria[]>('/v1/coloquios')
  return data
}

export async function createColoquio(payload: ColoquioCreate): Promise<ColoquioConvocatoria> {
  const { data } = await api.post<ColoquioConvocatoria>('/v1/coloquios', payload)
  return data
}

export async function patchColoquio(id: string, payload: ColoquioPatch): Promise<ColoquioConvocatoria> {
  const { data } = await api.patch<ColoquioConvocatoria>(`/v1/coloquios/${id}`, payload)
  return data
}

export async function deleteColoquio(id: string): Promise<void> {
  await api.delete(`/v1/coloquios/${id}`)
}
