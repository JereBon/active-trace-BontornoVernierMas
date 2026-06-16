// __tests__/TrackingLotePanel.test.tsx
// TDD tests for TrackingLotePanel — counters, polling, terminal state.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TrackingLotePanel } from '../components/TrackingLotePanel'

vi.mock('../services/comunicacionesService', () => ({
  getLoteStatus: vi.fn(),
}))

import { getLoteStatus } from '../services/comunicacionesService'
const mockGetLote = getLoteStatus as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const pendingLote = {
  lote_id: 'lote-1',
  total: 5,
  pendientes: 3,
  enviados: 2,
  errores: 0,
  cancelados: 0,
  mensajes: [],
}

const terminalLote = {
  ...pendingLote,
  pendientes: 0,
  enviados: 5,
}

describe('TrackingLotePanel', () => {
  beforeEach(() => { vi.clearAllMocks() })

  // RED: counters show correct initial values
  it('renders initial counters from lote status', async () => {
    mockGetLote.mockResolvedValueOnce(pendingLote)

    render(<TrackingLotePanel loteId="lote-1" />, { wrapper })

    const counters = await screen.findByTestId('lote-counters')
    expect(counters).toBeTruthy()
    expect(screen.getByText('3')).toBeTruthy() // pendientes
    expect(screen.getByText('2')).toBeTruthy() // enviados
  })

  // GREEN: terminal state shows "Completado" badge
  it('shows Completado badge when all messages are in terminal state', async () => {
    mockGetLote.mockResolvedValueOnce(terminalLote)

    render(<TrackingLotePanel loteId="lote-1" />, { wrapper })

    const badge = await screen.findByText(/completado/i)
    expect(badge).toBeTruthy()
  })

  // Triangulation: "Actualizando" text shown while pendientes > 0
  it('shows updating indicator while there are pending messages', async () => {
    mockGetLote.mockResolvedValueOnce(pendingLote)

    render(<TrackingLotePanel loteId="lote-1" />, { wrapper })

    const updating = await screen.findByText(/actualizando/i)
    expect(updating).toBeTruthy()
  })
})
