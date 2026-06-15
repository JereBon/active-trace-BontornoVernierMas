// features/comision/hooks/useMonitor.ts
import { useQuery } from '@tanstack/react-query'
import { getMonitor } from '../services/analisisService'
import { isUuid } from '@/shared/utils/isUuid'
import type { MonitorItem, MonitorParams } from '../types'

export function useMonitor(params: MonitorParams) {
  return useQuery<MonitorItem[], Error>({
    queryKey: ['monitor', params],
    queryFn: () => getMonitor(params),
    enabled: isUuid(params.materia_id),
  })
}
