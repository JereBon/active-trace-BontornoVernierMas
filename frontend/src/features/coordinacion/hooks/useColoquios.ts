// features/coordinacion/hooks/useColoquios.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createColoquio, deleteColoquio, getColoquios, patchColoquio } from '../services/coloquiosService'
import type { ColoquioCreate, ColoquioPatch } from '../types'

const QUERY_KEY = ['coloquios']

export function useColoquios() {
  return useQuery({ queryKey: QUERY_KEY, queryFn: getColoquios })
}

export function useCreateColoquio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ColoquioCreate) => createColoquio(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function usePatchColoquio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ColoquioPatch }) =>
      patchColoquio(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useDeleteColoquio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteColoquio(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
