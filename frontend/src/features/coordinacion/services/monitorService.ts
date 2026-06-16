// features/coordinacion/services/monitorService.ts
// Reuses the /v1/analisis/monitor endpoint without materia filter — global view for COORDINADOR
import { api } from '@/shared/services/api'
import type { MonitorItem } from '@/features/comision/types'

export interface MonitorGlobalParams {
  comision?: string
  regional?: string
}

export async function getMonitorGlobal(params: MonitorGlobalParams = {}): Promise<MonitorItem[]> {
  const { data } = await api.get<MonitorItem[]>('/v1/analisis/monitor', { params })
  return data
}
