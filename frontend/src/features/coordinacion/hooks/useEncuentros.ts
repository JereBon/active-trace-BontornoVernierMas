// features/coordinacion/hooks/useEncuentros.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createEncuentro, getEncuentros } from '../services/encuentrosService'
import type { EncuentroCreate } from '../types'

const QUERY_KEY = ['encuentros']

export function useEncuentros() {
  return useQuery({ queryKey: QUERY_KEY, queryFn: getEncuentros })
}

export function useCreateEncuentro() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: EncuentroCreate) => createEncuentro(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
