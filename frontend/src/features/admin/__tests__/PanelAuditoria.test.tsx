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
    total_acciones: 1500,
    acciones_hoy: 42,
    top_acciones: [
      { accion: 'login', cantidad: 800 },
      { accion: 'crear_comunicacion', cantidad: 200 },
    ],
    top_actores: [],
    ...overrides,
  }
}

function makeLog(items: Partial<LogPaginado['items'][0]>[] = []): LogPaginado {
  return {
    total: items.length,
    offset: 0,
    limit: 50,
    items: items.map((item, i) => ({
      id: `log-${i}`,
      actor_id: 'u-1',
      actor_nombre: 'Admin User',
      accion: 'login',
      recurso_tipo: null,
      recurso_id: null,
      detalle: null,
      ip: '127.0.0.1',
      created_at: '2024-03-15T10:00:00Z',
      ...item,
    })),
  }
}

describe('PanelAuditoria', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renderiza métricas total_acciones y acciones_hoy', async () => {
    mockGetPanel.mockResolvedValueOnce(makePanel({ total_acciones: 2500, acciones_hoy: 100 }))
    mockGetLog.mockResolvedValueOnce(makeLog([]))

    render(<PanelAuditoria />, { wrapper })

    // toLocaleString() output depends on the test environment locale; match on partial text
    const totalEl = await screen.findByText(/2.?500/)
    expect(totalEl).toBeTruthy()
    const hoyEl = screen.getByText('100')
    expect(hoyEl).toBeTruthy()
  })

  it('renderiza top acciones en el panel de métricas', async () => {
    mockGetPanel.mockResolvedValueOnce(makePanel())
    mockGetLog.mockResolvedValueOnce(makeLog([]))

    render(<PanelAuditoria />, { wrapper })

    expect(await screen.findByText('login')).toBeTruthy()
    expect(screen.getByText('crear_comunicacion')).toBeTruthy()
  })

  it('renderiza filas del log con actor y acción', async () => {
    mockGetPanel.mockResolvedValueOnce(makePanel())
    mockGetLog.mockResolvedValueOnce(
      makeLog([
        { actor_nombre: 'María Admin', accion: 'cerrar_liquidacion' },
        { actor_nombre: 'Carlos User', accion: 'login', id: 'log-99' },
      ]),
    )

    render(<PanelAuditoria />, { wrapper })

    expect(await screen.findByText('María Admin')).toBeTruthy()
    expect(screen.getByText('cerrar_liquidacion')).toBeTruthy()
    expect(screen.getByText('Carlos User')).toBeTruthy()
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
