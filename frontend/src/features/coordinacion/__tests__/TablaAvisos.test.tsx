// __tests__/TablaAvisos.test.tsx
// TDD tests for TablaAvisos — render activos/archivados, badge severidad, botón archivar.

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
    titulo: 'Aviso de prueba',
    cuerpo: 'Contenido del aviso',
    scope: 'todos',
    severidad: 'info',
    vigencia_hasta: null,
    requiere_ack: false,
    archivado: false,
    created_at: '2024-01-01T00:00:00Z',
    tenant_id: 'tenant-1',
    ...overrides,
  }
}

describe('TablaAvisos', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders aviso rows with title and severity badge', async () => {
    mockGetAvisos.mockResolvedValueOnce([
      makeAviso({ titulo: 'Aviso Crítico', severidad: 'critico' }),
      makeAviso({ titulo: 'Aviso Info', severidad: 'info' }),
    ])

    render(<TablaAvisos />, { wrapper })

    expect(await screen.findByText('Aviso Crítico')).toBeTruthy()
    expect(screen.getByText('Aviso Info')).toBeTruthy()
    // Severity badge for critico
    expect(screen.getByText(/critico/i)).toBeTruthy()
  })

  it('shows empty state when no avisos exist', async () => {
    mockGetAvisos.mockResolvedValueOnce([])

    render(<TablaAvisos />, { wrapper })

    const msg = await screen.findByText(/no hay avisos/i)
    expect(msg).toBeTruthy()
  })

  it('renders archivar button for active avisos', async () => {
    mockGetAvisos.mockResolvedValueOnce([
      makeAviso({ titulo: 'Aviso Activo', archivado: false }),
    ])

    render(<TablaAvisos />, { wrapper })

    const btn = await screen.findByRole('button', { name: /archivar/i })
    expect(btn).toBeTruthy()
  })

  it('does not show archivar button for already archived avisos', async () => {
    mockGetAvisos.mockResolvedValueOnce([
      makeAviso({ titulo: 'Aviso Archivado', archivado: true }),
    ])

    render(<TablaAvisos />, { wrapper })

    await screen.findByText('Aviso Archivado')
    expect(screen.queryByRole('button', { name: /archivar/i })).toBeNull()
  })
})
