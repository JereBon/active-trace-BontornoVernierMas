// features/finanzas/services/liquidacionesService.ts
import { api } from '@/shared/services/api'
import type {
  CalcularRequest,
  CalcularResponse,
  CerrarRequest,
  CerrarResponse,
  LiquidacionRow,
  VistaPeriodoOut,
} from '../types'

export async function getVistaPeriodo(
  cohorte_id: string,
  periodo: string,
): Promise<VistaPeriodoOut> {
  const { data } = await api.get<VistaPeriodoOut>('/v1/liquidaciones/', {
    params: { cohorte_id, periodo },
  })
  return data
}

export async function calcularLiquidaciones(
  payload: CalcularRequest,
): Promise<CalcularResponse> {
  const { data } = await api.post<CalcularResponse>('/v1/liquidaciones/calcular', payload)
  return data
}

export async function cerrarPeriodo(payload: CerrarRequest): Promise<CerrarResponse> {
  const { data } = await api.post<CerrarResponse>('/v1/liquidaciones/cerrar', payload)
  return data
}

export async function getHistorial(
  cohorte_id?: string,
  periodo?: string,
): Promise<LiquidacionRow[]> {
  const { data } = await api.get<LiquidacionRow[]>('/v1/liquidaciones/historial', {
    params: { cohorte_id, periodo },
  })
  return data
}
