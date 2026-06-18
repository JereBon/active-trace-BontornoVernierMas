// features/coordinacion/services/coloquiosService.ts
import { api } from '@/shared/services/api'
import type { EvaluacionCreate, EvaluacionMetricas, EvaluacionOut } from '../types'

export async function getColoquios(): Promise<EvaluacionOut[]> {
  const { data } = await api.get<EvaluacionOut[]>('/v1/coloquios')
  return data
}

export async function getMetricasColoquios(): Promise<EvaluacionMetricas> {
  const { data } = await api.get<EvaluacionMetricas>('/v1/coloquios/metricas')
  return data
}

export async function createColoquio(payload: EvaluacionCreate): Promise<EvaluacionOut> {
  const { data } = await api.post<EvaluacionOut>('/v1/coloquios', payload)
  return data
}

export async function updateColoquio(id: string, payload: Partial<EvaluacionCreate>): Promise<EvaluacionOut> {
  const { data } = await api.patch<EvaluacionOut>(`/v1/coloquios/${id}`, payload)
  return data
}

export async function deleteColoquio(id: string): Promise<void> {
  await api.delete(`/v1/coloquios/${id}`)
}
