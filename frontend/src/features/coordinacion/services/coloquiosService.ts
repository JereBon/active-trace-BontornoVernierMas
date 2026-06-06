// features/coordinacion/services/coloquiosService.ts
import { api } from '@/shared/services/api'
import type { ColoquioConvocatoria, ColoquioCreate } from '../types'

export async function getColoquios(): Promise<ColoquioConvocatoria[]> {
  const { data } = await api.get<ColoquioConvocatoria[]>('/v1/coloquios')
  return data
}

export async function createColoquio(payload: ColoquioCreate): Promise<ColoquioConvocatoria> {
  const { data } = await api.post<ColoquioConvocatoria>('/v1/coloquios', payload)
  return data
}
