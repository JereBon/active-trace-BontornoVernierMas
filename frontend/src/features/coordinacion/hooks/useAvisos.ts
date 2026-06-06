// features/coordinacion/hooks/useAvisos.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { archivarAviso, createAviso, getAvisos, updateAviso } from '../services/avisosService'
import type { AvisoCreate } from '../types'

const QUERY_KEY = ['avisos']

export function useAvisos() {
  return useQuery({ queryKey: QUERY_KEY, queryFn: getAvisos })
}

export function useCreateAviso() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AvisoCreate) => createAviso(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useUpdateAviso() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<AvisoCreate> }) =>
      updateAviso(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useArchivarAviso() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => archivarAviso(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
