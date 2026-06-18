// features/coordinacion/hooks/useEncuentros.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createSlot, getEncuentros, updateInstancia } from '../services/encuentrosService'
import type { InstanciaUpdate, SlotCreate } from '../types'

const QUERY_KEY = ['encuentros-admin']

export function useEncuentros() {
  return useQuery({ queryKey: QUERY_KEY, queryFn: getEncuentros })
}

export function useCreateSlot() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SlotCreate) => createSlot(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useUpdateInstancia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: InstanciaUpdate }) =>
      updateInstancia(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
