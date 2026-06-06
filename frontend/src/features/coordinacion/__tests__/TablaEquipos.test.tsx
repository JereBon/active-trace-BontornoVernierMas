// __tests__/TablaEquipos.test.tsx
// TDD tests for TablaEquipos — render with data, empty state, pagination.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TablaEquipos } from '../components/equipos/TablaEquipos'
import type { EquipoDocente } from '../types'

vi.mock('../services/equiposService', () => ({
  getEquipos: vi.fn(),
  deleteEquipo: vi.fn(),
}))

import { getEquipos } from '../services/equiposService'
const mockGetEquipos = getEquipos as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeEquipo(overrides: Partial<EquipoDocente> = {}): EquipoDocente {
  return {
    id: crypto.randomUUID(),
    nombre: 'Equipo A',
    descripcion: null,
    vigencia_desde: '2024-03-01',
    vigencia_hasta: '2024-07-31',
    integrantes: [],
    tenant_id: 'tenant-1',
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('TablaEquipos', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders equipo rows when data is available', async () => {
    mockGetEquipos.mockResolvedValueOnce([
      makeEquipo({ nombre: 'Equipo Matemáticas' }),
      makeEquipo({ nombre: 'Equipo Física' }),
    ])

    render(<TablaEquipos onEdit={vi.fn()} />, { wrapper })

    const row1 = await screen.findByText('Equipo Matemáticas')
    const row2 = await screen.findByText('Equipo Física')
    expect(row1).toBeTruthy()
    expect(row2).toBeTruthy()
  })

  it('shows empty state message when no equipos exist', async () => {
    mockGetEquipos.mockResolvedValueOnce([])

    render(<TablaEquipos onEdit={vi.fn()} />, { wrapper })

    const msg = await screen.findByText(/no hay equipos/i)
    expect(msg).toBeTruthy()
  })

  it('shows pagination when there are more than 20 equipos', async () => {
    const items = Array.from({ length: 25 }, (_, i) =>
      makeEquipo({ nombre: `Equipo ${i}`, id: `id-${i}` }),
    )
    mockGetEquipos.mockResolvedValueOnce(items)

    render(<TablaEquipos onEdit={vi.fn()} />, { wrapper })

    const nextBtn = await screen.findByRole('button', { name: /siguiente/i })
    expect(nextBtn).not.toBeDisabled()

    // Page 1 shows first 20
    expect(screen.queryByText('Equipo 24')).toBeNull()

    fireEvent.click(nextBtn)
    expect(screen.getByText('Equipo 24')).toBeTruthy()
  })
})
