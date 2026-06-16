// __tests__/TablaAvisos.test.tsx
// TDD tests for TablaAvisos — render activos/archivados, botón archivar.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TablaAvisos } from '../components/avisos/TablaAvisos'
import type { Aviso } from '../types'

vi.mock('../services/avisosService', () => ({
  getAvisos: vi.fn(),
  archivarAviso: vi.fn(),
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
    tenant_id: 'tenant-1',
    titulo: 'Aviso de prueba',
    cuerpo: 'Contenido del aviso',
    scope: 'TODOS',
    scope_valor: null,
    vig_desde: '2024-06-01T00:00:00Z',
    vig_hasta: '2024-12-31T23:59:00Z',
    activo: true,
    publicado_por: crypto.randomUUID(),
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('TablaAvisos', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders aviso rows with title and scope', async () => {
    mockGetAvisos.mockResolvedValueOnce([
      makeAviso({ titulo: 'Aviso General', scope: 'TODOS' }),
      makeAviso({ titulo: 'Aviso Coordinadores', scope: 'ROL', scope_valor: 'COORDINADOR' }),
    ])

    render(<TablaAvisos />, { wrapper })

    expect(await screen.findByText('Aviso General')).toBeTruthy()
    expect(screen.getByText('Aviso Coordinadores')).toBeTruthy()
  })

  it('shows empty state when no avisos exist', async () => {
    mockGetAvisos.mockResolvedValueOnce([])

    render(<TablaAvisos />, { wrapper })

    const msg = await screen.findByText(/no hay avisos/i)
    expect(msg).toBeTruthy()
  })

  it('renders archivar button for active avisos', async () => {
    mockGetAvisos.mockResolvedValueOnce([
      makeAviso({ titulo: 'Aviso Activo', activo: true }),
    ])

    render(<TablaAvisos />, { wrapper })

    const btn = await screen.findByRole('button', { name: /archivar/i })
    expect(btn).toBeTruthy()
  })

  it('does not show archivar button for already archived avisos', async () => {
    mockGetAvisos.mockResolvedValueOnce([
      makeAviso({ titulo: 'Aviso Archivado', activo: false }),
    ])

    render(<TablaAvisos />, { wrapper })

    await screen.findByText('Aviso Archivado')
    expect(screen.queryByRole('button', { name: /archivar/i })).toBeNull()
  })
})
