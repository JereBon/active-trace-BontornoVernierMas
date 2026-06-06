// features/comision/hooks/useMonitor.ts
import { useQuery } from '@tanstack/react-query'
import { getMonitor } from '../services/analisisService'
import type { MonitorItem, MonitorParams } from '../types'

export function useMonitor(params: MonitorParams) {
  return useQuery<MonitorItem[], Error>({
    queryKey: ['monitor', params],
    queryFn: () => getMonitor(params),
  })
}
