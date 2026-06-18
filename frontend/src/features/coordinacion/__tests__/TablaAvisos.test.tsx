// __tests__/TablaAvisos.test.tsx
// TDD tests for TablaAvisos — render activos/inactivos, botón desactivar.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TablaAvisos } from '../components/avisos/TablaAvisos'
import type { Aviso } from '../types'

vi.mock('../services/avisosService', () => ({
  getAvisos: vi.fn(),
  desactivarAviso: vi.fn(),
}))

import { getAvisos } from '../services/avisosService'
const mockGetAvisos = getAvisos as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeAviso(overrides: Partial<Aviso> = {}): Aviso {
  return {
    id: crypto.randomUUID(),
    titulo: 'Aviso de prueba',
    cuerpo: 'Contenido del aviso',
    scope: 'TODOS',
    scope_valor: null,
    vig_desde: '2024-01-01T00:00:00Z',
    vig_hasta: '2025-01-01T00:00:00Z',
    activo: true,
    publicado_por: crypto.randomUUID(),
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    tenant_id: 'tenant-1',
    ...overrides,
  }
}

describe('TablaAvisos', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders aviso rows with title', async () => {
    mockGetAvisos.mockResolvedValueOnce([
      makeAviso({ titulo: 'Aviso Importante' }),
      makeAviso({ titulo: 'Aviso Info' }),
    ])

    render(<TablaAvisos />, { wrapper })

    expect(await screen.findByText('Aviso Importante')).toBeTruthy()
    expect(screen.getByText('Aviso Info')).toBeTruthy()
  })

  it('shows empty state when no avisos exist', async () => {
    mockGetAvisos.mockResolvedValueOnce([])

    render(<TablaAvisos />, { wrapper })

    const msg = await screen.findByText(/no hay avisos/i)
    expect(msg).toBeTruthy()
  })

  it('renders desactivar button for active avisos', async () => {
    mockGetAvisos.mockResolvedValueOnce([
      makeAviso({ titulo: 'Aviso Activo', activo: true }),
    ])

    render(<TablaAvisos />, { wrapper })

    const btn = await screen.findByRole('button', { name: /desactivar/i })
    expect(btn).toBeTruthy()
  })

  it('does not show desactivar button for already inactive avisos', async () => {
    mockGetAvisos.mockResolvedValueOnce([
      makeAviso({ titulo: 'Aviso Inactivo', activo: false }),
    ])

    render(<TablaAvisos />, { wrapper })

    await screen.findByText('Aviso Inactivo')
    expect(screen.queryByRole('button', { name: /desactivar/i })).toBeNull()
  })
})
