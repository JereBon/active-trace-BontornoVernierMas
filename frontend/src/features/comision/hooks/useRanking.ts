// features/comision/hooks/useRanking.ts
import { useQuery } from '@tanstack/react-query'
import { isUuid } from '@/shared/utils/isUuid'
import { getRanking } from '../services/analisisService'
import type { RankingItem } from '../types'

export function useRanking(materiaId: string) {
  return useQuery<RankingItem[], Error>({
    queryKey: ['ranking', materiaId],
    queryFn: () => getRanking(materiaId),
    enabled: isUuid(materiaId),
  })
}
