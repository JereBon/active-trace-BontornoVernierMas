// features/finanzas/hooks/useGrilla.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createSalarioBase,
  createSalarioPlus,
  getSalariosBase,
  getSalariosPlus,
  updateSalarioBase,
  updateSalarioPlus,
} from '../services/grillaService'
import type {
  SalarioBaseCreate,
  SalarioBaseUpdate,
  SalarioPlusCreate,
  SalarioPlusUpdate,
} from '../types'

const BASE_KEY = ['grilla-base']
const PLUS_KEY = ['grilla-plus']

export function useSalariosBase() {
  return useQuery({ queryKey: BASE_KEY, queryFn: getSalariosBase })
}

export function useCreateSalarioBase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SalarioBaseCreate) => createSalarioBase(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: BASE_KEY }),
  })
}

export function useUpdateSalarioBase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SalarioBaseUpdate }) =>
      updateSalarioBase(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: BASE_KEY }),
  })
}

export function useSalariosPlus() {
  return useQuery({ queryKey: PLUS_KEY, queryFn: getSalariosPlus })
}

export function useCreateSalarioPlus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SalarioPlusCreate) => createSalarioPlus(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: PLUS_KEY }),
  })
}

export function useUpdateSalarioPlus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SalarioPlusUpdate }) =>
      updateSalarioPlus(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: PLUS_KEY }),
  })
}
