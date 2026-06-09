// features/coordinacion/hooks/useMonitorGlobal.ts
import { useQuery } from '@tanstack/react-query'
import { getMonitorGlobal, type MonitorGlobalParams } from '../services/monitorService'
import type { MonitorItem } from '@/features/comision/types'

export function useMonitorGlobal(params: MonitorGlobalParams = {}) {
  return useQuery<MonitorItem[], Error>({
    queryKey: ['monitor-global', params],
    queryFn: () => getMonitorGlobal(params),
  })
}
