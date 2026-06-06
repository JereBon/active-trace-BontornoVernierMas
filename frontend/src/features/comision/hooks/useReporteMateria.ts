// features/comision/hooks/useReporteMateria.ts
import { useQuery } from '@tanstack/react-query'
import { getReporteMateria } from '../services/analisisService'
import type { ReporteMateria } from '../types'

export function useReporteMateria(materiaId: string) {
  return useQuery<ReporteMateria, Error>({
    queryKey: ['reporte-materia', materiaId],
    queryFn: () => getReporteMateria(materiaId),
    enabled: Boolean(materiaId),
  })
}
