// features/comision/hooks/useAtrasados.ts
import { useQuery } from '@tanstack/react-query'
import { getAtrasados } from '../services/analisisService'
import type { AtrasadoItem } from '../types'

export function useAtrasados(materiaId: string) {
  return useQuery<AtrasadoItem[], Error>({
    queryKey: ['atrasados', materiaId],
    queryFn: () => getAtrasados(materiaId),
    enabled: Boolean(materiaId),
  })
}
