import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  asignacionMasiva,
  clonarEquipo,
  createAsignacion,
  deleteAsignacion,
  getAsignaciones,
  updateAsignacion,
  vigenciaMasiva,
} from '../services/equiposService'
import type {
  AsignacionCreate,
  AsignacionFilter,
  AsignacionMasivaPayload,
  AsignacionUpdate,
  ClonarEquipoPayload,
  VigenciaMasivaPayload,
} from '../types'

const QUERY_KEY = ['asignaciones']

export function useEquipos(filters?: AsignacionFilter) {
  return useQuery({
    queryKey: filters ? [...QUERY_KEY, filters] : QUERY_KEY,
    queryFn: () => getAsignaciones(filters),
  })
}

export function useCreateEquipo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AsignacionCreate) => createAsignacion(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useUpdateEquipo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: AsignacionUpdate }) =>
      updateAsignacion(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useDeleteEquipo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteAsignacion(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useAsignacionMasiva() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AsignacionMasivaPayload) => asignacionMasiva(payload),
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

export function useVigenciaMasiva() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: VigenciaMasivaPayload) => vigenciaMasiva(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
