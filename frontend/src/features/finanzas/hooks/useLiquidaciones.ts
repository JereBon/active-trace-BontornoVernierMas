// features/finanzas/hooks/useLiquidaciones.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  calcularLiquidaciones,
  cerrarPeriodo,
  getHistorial,
  getVistaPeriodo,
} from '../services/liquidacionesService'
import type { CalcularRequest, CerrarRequest } from '../types'

const VISTA_KEY = (cohorteId: string, periodo: string) => [
  'liquidaciones-vista',
  cohorteId,
  periodo,
]
const HISTORIAL_KEY = ['liquidaciones-historial']

export function useVistaPeriodo(cohorteId: string, periodo: string) {
  return useQuery({
    queryKey: VISTA_KEY(cohorteId, periodo),
    queryFn: () => getVistaPeriodo(cohorteId, periodo),
    enabled: Boolean(cohorteId && periodo),
  })
}

export function useHistorial(cohorteId?: string, periodo?: string) {
  return useQuery({
    queryKey: [...HISTORIAL_KEY, cohorteId, periodo],
    queryFn: () => getHistorial(cohorteId, periodo),
  })
}

export function useCalcularLiquidaciones() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CalcularRequest) => calcularLiquidaciones(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['liquidaciones-vista'] }),
  })
}

export function useCerrarPeriodo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CerrarRequest) => cerrarPeriodo(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['liquidaciones-vista'] })
      qc.invalidateQueries({ queryKey: HISTORIAL_KEY })
    },
  })
}
