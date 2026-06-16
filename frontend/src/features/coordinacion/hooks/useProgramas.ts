// features/coordinacion/hooks/useProgramas.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createPrograma, deletePrograma, getProgramas } from '../services/programasService'
import type { ProgramaCreate } from '../services/programasService'

const PROGRAMAS_KEY = ['programas']

export function useProgramas() {
  return useQuery({ queryKey: PROGRAMAS_KEY, queryFn: getProgramas })
}

export function useCreatePrograma() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ProgramaCreate) => createPrograma(payload),
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
