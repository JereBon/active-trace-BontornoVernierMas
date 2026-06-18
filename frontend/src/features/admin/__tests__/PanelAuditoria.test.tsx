// __tests__/PanelAuditoria.test.tsx
// TDD tests for PanelAuditoria — renderiza métricas + tabla de log con filtros.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PanelAuditoria } from '../components/PanelAuditoria'
import type { LogPaginado, PanelMetricas } from '../types'

vi.mock('../services/auditoriaService', () => ({
  getPanelMetricas: vi.fn(),
  getAuditoriaLog: vi.fn(),
}))

import { getAuditoriaLog, getPanelMetricas } from '../services/auditoriaService'
const mockGetPanel = getPanelMetricas as ReturnType<typeof vi.fn>
const mockGetLog = getAuditoriaLog as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makePanel(overrides: Partial<PanelMetricas> = {}): PanelMetricas {
  return {
    acciones_por_dia: [
      { fecha: '2024-03-15', total: 2500 },
      { fecha: '2024-03-14', total: 1000 },
    ],
    por_docente: [
      { actor_id: 'u-1', total: 800 },
      { actor_id: 'u-2', total: 200 },
    ],
    por_materia: [],
    ...overrides,
  }
}

function makeLog(items: Partial<LogPaginado['items'][0]>[] = []): LogPaginado {
  return {
    total: items.length,
    items: items.map((item, i) => ({
      id: `log-${i}`,
      tenant_id: 'tenant-1',
      actor_id: 'u-1',
      actor_impersonado_id: null,
      accion: 'login',
      detalle: null,
      filas_afectadas: 0,
      ip: '127.0.0.1',
      user_agent: 'Mozilla/5.0',
      fecha_hora: '2024-03-15T10:00:00Z',
      ...item,
    })),
  }
}

describe('PanelAuditoria', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renderiza total_acciones sumando acciones_por_dia', async () => {
    mockGetPanel.mockResolvedValueOnce(makePanel())
    mockGetLog.mockResolvedValueOnce(makeLog([]))

    render(<PanelAuditoria />, { wrapper })

    // Total: 2500 + 1000 = 3500
    const totalEl = await screen.findByText(/3.?500/)
    expect(totalEl).toBeTruthy()
  })

  it('renderiza la sección de acciones por día', async () => {
    mockGetPanel.mockResolvedValueOnce(makePanel())
    mockGetLog.mockResolvedValueOnce(makeLog([]))

    render(<PanelAuditoria />, { wrapper })

    expect(await screen.findByText('2024-03-15')).toBeTruthy()
    expect(screen.getByText('2024-03-14')).toBeTruthy()
  })

  it('renderiza filas del log con actor y acción', async () => {
    mockGetPanel.mockResolvedValueOnce(makePanel())
    mockGetLog.mockResolvedValueOnce(
      makeLog([
        { actor_id: 'actor-uuid-1', accion: 'cerrar_liquidacion' },
        { actor_id: 'actor-uuid-2', accion: 'login', id: 'log-99' },
      ]),
    )

    render(<PanelAuditoria />, { wrapper })

    expect(await screen.findByText('cerrar_liquidacion')).toBeTruthy()
    expect(screen.getByText('login')).toBeTruthy()
  })

  it('muestra mensaje vacío cuando el log no tiene entradas', async () => {
    mockGetPanel.mockResolvedValueOnce(makePanel())
    mockGetLog.mockResolvedValueOnce(makeLog([]))

    render(<PanelAuditoria />, { wrapper })

    await screen.findByText(/total acciones/i)
    const msg = await screen.findByText(/no hay entradas/i)
    expect(msg).toBeTruthy()
  })
})
