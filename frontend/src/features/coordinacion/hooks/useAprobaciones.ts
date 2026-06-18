// features/coordinacion/hooks/useAprobaciones.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { aprobarLote, cancelarLote, getLoteStatus, getLotesByMateria } from '../services/aprobacionesService'

export function useLotesByMateria(materiaId: string | null) {
  return useQuery({
    queryKey: ['lotes-materia', materiaId],
    queryFn: () => getLotesByMateria(materiaId!),
    enabled: !!materiaId,
  })
}

export function useLoteStatus(loteId: string | null) {
  return useQuery({
    queryKey: ['lote', loteId],
    queryFn: () => getLoteStatus(loteId!),
    enabled: !!loteId,
  })
}

export function useAprobarLote(loteId: string | null) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => aprobarLote(loteId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lote', loteId] })
      qc.invalidateQueries({ queryKey: ['lotes-materia'] })
    },
  })
}

export function useCancelarLote(loteId: string | null) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => cancelarLote(loteId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lote', loteId] })
      qc.invalidateQueries({ queryKey: ['lotes-materia'] })
    },
  })
}
