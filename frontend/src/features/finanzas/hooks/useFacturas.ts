// features/finanzas/hooks/useFacturas.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { cambiarEstadoFactura, createFactura, getFacturas } from '../services/facturasService'
import type { FacturaCreate, FacturaEstado, FacturaFiltros } from '../types'

const FACTURAS_KEY = ['facturas']

export function useFacturas(filtros?: FacturaFiltros) {
  return useQuery({
    queryKey: [...FACTURAS_KEY, filtros],
    queryFn: () => getFacturas(filtros),
  })
}

export function useCreateFactura() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: FacturaCreate) => createFactura(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: FACTURAS_KEY }),
  })
}

export function useCambiarEstadoFactura() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: FacturaEstado }) =>
      cambiarEstadoFactura(id, estado),
    onSuccess: () => qc.invalidateQueries({ queryKey: FACTURAS_KEY }),
  })
}
