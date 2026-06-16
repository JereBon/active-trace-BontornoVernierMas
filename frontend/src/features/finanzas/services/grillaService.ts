// features/finanzas/services/grillaService.ts
import { api } from '@/shared/services/api'
import type {
  SalarioBase,
  SalarioBaseCreate,
  SalarioBaseUpdate,
  SalarioPlus,
  SalarioPlusCreate,
  SalarioPlusUpdate,
} from '../types'

// ─── SalarioBase ──────────────────────────────────────────────────────────────

export async function getSalariosBase(): Promise<SalarioBase[]> {
  const { data } = await api.get<SalarioBase[]>('/v1/liquidaciones/grilla/base')
  return data
}

export async function createSalarioBase(payload: SalarioBaseCreate): Promise<SalarioBase> {
  const { data } = await api.post<SalarioBase>('/v1/liquidaciones/grilla/base', payload)
  return data
}

export async function updateSalarioBase(
  id: string,
  payload: SalarioBaseUpdate,
): Promise<SalarioBase> {
  const { data } = await api.put<SalarioBase>(`/v1/liquidaciones/grilla/base/${id}`, payload)
  return data
}

// ─── SalarioPlus ─────────────────────────────────────────────────────────────

export async function getSalariosPlus(): Promise<SalarioPlus[]> {
  const { data } = await api.get<SalarioPlus[]>('/v1/liquidaciones/grilla/plus')
  return data
}

export async function createSalarioPlus(payload: SalarioPlusCreate): Promise<SalarioPlus> {
  const { data } = await api.post<SalarioPlus>('/v1/liquidaciones/grilla/plus', payload)
  return data
}

export async function updateSalarioPlus(
  id: string,
  payload: SalarioPlusUpdate,
): Promise<SalarioPlus> {
  const { data } = await api.put<SalarioPlus>(`/v1/liquidaciones/grilla/plus/${id}`, payload)
  return data
}
