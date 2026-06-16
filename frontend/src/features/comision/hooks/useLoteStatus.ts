// features/comision/hooks/useLoteStatus.ts
// Polls every 3 seconds until a terminal state is reached.
import { useQuery } from '@tanstack/react-query'
import { getLoteStatus } from '../services/comunicacionesService'
import type { LoteStatus } from '../types'

const TERMINAL_STATES = new Set(['Enviado', 'Fallido', 'Cancelado'])
const POLL_INTERVAL_MS = 3000
const MAX_POLL_MS = 2 * 60 * 1000 // 2 minutes

function isTerminal(data: LoteStatus | undefined): boolean {
  if (!data) return false
  // Terminal when all messages are in a terminal state
  return data.pendientes === 0
}

export function useLoteStatus(loteId: string | null) {
  return useQuery<LoteStatus, Error>({
    queryKey: ['lote-status', loteId],
    queryFn: () => getLoteStatus(loteId as string),
    enabled: Boolean(loteId),
    refetchInterval: (query) => {
      const data = query.state.data
      if (isTerminal(data)) return false
      return POLL_INTERVAL_MS
    },
    // Stop polling after 2 minutes regardless
    staleTime: MAX_POLL_MS,
  })
}

export { TERMINAL_STATES }
