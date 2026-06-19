import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getProgramas,
  getProgramasByMateria,
  createPrograma,
  deletePrograma,
} from '@/features/coordinacion/services/programasService'
import type { ProgramaMateriaCreate } from '@/features/coordinacion/services/programasService'

const PROGRAMAS_KEY = ['programas']

export function useProgramas() {
  return useQuery({ queryKey: PROGRAMAS_KEY, queryFn: getProgramas })
}

export function useProgramasByMateria(materiaId: string | null) {
  return useQuery({
    queryKey: [...PROGRAMAS_KEY, 'materia', materiaId],
    queryFn: () => getProgramasByMateria(materiaId!),
    enabled: Boolean(materiaId),
  })
}

export function useCreatePrograma() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ProgramaMateriaCreate) => createPrograma(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: PROGRAMAS_KEY }),
  })
}

export function useDeletePrograma() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deletePrograma(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: PROGRAMAS_KEY }),
  })
}
