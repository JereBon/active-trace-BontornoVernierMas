// features/coordinacion/hooks/useEquipos.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  clonarEquipo,
  createEquipo,
  deleteEquipo,
  getEquipos,
  updateEquipo,
} from '../services/equiposService'
import type { ClonarEquipoPayload } from '../services/equiposService'
import type { EquipoDocenteCreate, EquipoDocenteUpdate } from '../types'

const QUERY_KEY = ['equipos-docentes']

export function useEquipos(responsableId?: string) {
  return useQuery({
    queryKey: [...QUERY_KEY, responsableId ?? null],
    queryFn: () => getEquipos(responsableId),
  })
}

export function useCreateEquipo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: EquipoDocenteCreate) => createEquipo(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useUpdateEquipo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: EquipoDocenteUpdate }) =>
      updateEquipo(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useDeleteEquipo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteEquipo(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useClonarEquipo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ClonarEquipoPayload) => clonarEquipo(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
