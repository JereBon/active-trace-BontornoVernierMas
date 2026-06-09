// features/admin/hooks/useAuditoria.ts
import { useQuery } from '@tanstack/react-query'
import { getAuditoriaLog, getPanelMetricas } from '../services/auditoriaService'
import type { LogFiltros } from '../types'

const PANEL_KEY = ['auditoria-panel']
const LOG_KEY = ['auditoria-log']

export function usePanelMetricas() {
  return useQuery({ queryKey: PANEL_KEY, queryFn: getPanelMetricas })
}

export function useAuditoriaLog(filtros?: LogFiltros) {
  return useQuery({
    queryKey: [...LOG_KEY, filtros],
    queryFn: () => getAuditoriaLog(filtros),
  })
}
