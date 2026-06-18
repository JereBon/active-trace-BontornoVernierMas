// features/coordinacion/hooks/useColoquios.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createColoquio, getColoquios, getMetricasColoquios, updateColoquio, deleteColoquio } from '../services/coloquiosService'
import type { EvaluacionCreate } from '../types'

const QUERY_KEY = ['coloquios']
const METRICAS_KEY = ['coloquios-metricas']

export function useColoquios() {
  return useQuery({ queryKey: QUERY_KEY, queryFn: getColoquios })
}

export function useMetricasColoquios() {
  return useQuery({ queryKey: METRICAS_KEY, queryFn: getMetricasColoquios })
}

export function useCreateColoquio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: EvaluacionCreate) => createColoquio(payload),
    onSuccess: () => { qc.invalidateQueries({ queryKey: QUERY_KEY }); qc.invalidateQueries({ queryKey: METRICAS_KEY }) },
  })
}

export function useUpdateColoquio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<EvaluacionCreate> }) =>
      updateColoquio(id, payload),
    onSuccess: () => { qc.invalidateQueries({ queryKey: QUERY_KEY }); qc.invalidateQueries({ queryKey: METRICAS_KEY }) },
  })
}

export function useDeleteColoquio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteColoquio(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: QUERY_KEY }); qc.invalidateQueries({ queryKey: METRICAS_KEY }) },
  })
}
