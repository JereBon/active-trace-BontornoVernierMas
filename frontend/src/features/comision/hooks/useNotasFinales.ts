// features/comision/hooks/useNotasFinales.ts
import { useQuery } from '@tanstack/react-query'
import { isUuid } from '@/shared/utils/isUuid'
import { getNotasFinales } from '../services/analisisService'
import type { NotaFinal } from '../types'

export function useNotasFinales(materiaId: string) {
  return useQuery<NotaFinal[], Error>({
    queryKey: ['notas-finales', materiaId],
    queryFn: () => getNotasFinales(materiaId),
    enabled: isUuid(materiaId),
  })
}
