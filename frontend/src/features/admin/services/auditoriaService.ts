// features/admin/services/auditoriaService.ts
import { api } from '@/shared/services/api'
import type { LogFiltros, LogPaginado, PanelMetricas } from '../types'

export async function getPanelMetricas(): Promise<PanelMetricas> {
  const { data } = await api.get<PanelMetricas>('/v1/auditoria/panel')
  return data
}

export async function getAuditoriaLog(filtros?: LogFiltros): Promise<LogPaginado> {
  const { data } = await api.get<LogPaginado>('/v1/auditoria/log', { params: filtros })
  return data
}
