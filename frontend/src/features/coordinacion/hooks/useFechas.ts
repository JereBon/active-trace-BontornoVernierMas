import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getFechas,
  createFecha,
  deleteFecha,
} from '@/features/coordinacion/services/fechasService'
import type { FechaAcademicaCreate } from '@/features/coordinacion/services/fechasService'

const FECHAS_KEY = ['fechas-academicas']

export function useFechas(materiaId?: string) {
  return useQuery({
    queryKey: [...FECHAS_KEY, materiaId],
    queryFn: () => getFechas(materiaId),
  })
}

export function useCreateFecha() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: FechaAcademicaCreate) => createFecha(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: FECHAS_KEY }),
  })
}

export function useDeleteFecha() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteFecha(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: FECHAS_KEY }),
  })
}
