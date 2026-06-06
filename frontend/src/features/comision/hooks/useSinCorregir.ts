// features/comision/hooks/useSinCorregir.ts
import { useQuery } from '@tanstack/react-query'
import { getSinCorregir } from '../services/analisisService'
import type { SinCorregirItem } from '../types'

export function useSinCorregir(materiaId: string) {
  return useQuery<SinCorregirItem[], Error>({
    queryKey: ['sin-corregir', materiaId],
    queryFn: () => getSinCorregir(materiaId),
    enabled: Boolean(materiaId),
  })
}
