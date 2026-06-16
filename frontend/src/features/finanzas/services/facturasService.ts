// features/finanzas/services/facturasService.ts
import { api } from '@/shared/services/api'
import type { Factura, FacturaCreate, FacturaEstado, FacturaFiltros } from '../types'

export async function getFacturas(filtros?: FacturaFiltros): Promise<Factura[]> {
  const { data } = await api.get<Factura[]>('/v1/facturas/', { params: filtros })
  return data
}

export async function createFactura(payload: FacturaCreate): Promise<Factura> {
  const { data } = await api.post<Factura>('/v1/facturas/', payload)
  return data
}

export async function cambiarEstadoFactura(
  id: string,
  estado: FacturaEstado,
): Promise<Factura> {
  const { data } = await api.patch<Factura>(`/v1/facturas/${id}/estado`, { estado })
  return data
}
