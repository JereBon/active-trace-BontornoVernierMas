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
    tenant_id: 'tenant-1',
    usuario_id: crypto.randomUUID(),
    rol: 'PROFESOR',
    materia_id: null,
    carrera_id: null,
    cohorte_id: null,
    comisiones: [],
    responsable_id: null,
    desde: '2024-03-01',
    hasta: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    deleted_at: null,
    ...overrides,
  }
}

describe('TablaEquipos', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders equipo rows when data is available', async () => {
    const uid1 = 'aaaaaaaa-0000-0000-0000-000000000001'
    const uid2 = 'bbbbbbbb-0000-0000-0000-000000000002'
    mockGetEquipos.mockResolvedValueOnce([
      makeEquipo({ usuario_id: uid1, rol: 'PROFESOR' }),
      makeEquipo({ usuario_id: uid2, rol: 'TUTOR' }),
    ])

    render(<TablaEquipos onEdit={vi.fn()} />, { wrapper })

    expect(await screen.findByText('PROFESOR')).toBeTruthy()
    expect(screen.getByText('TUTOR')).toBeTruthy()
  })

  it('shows empty state message when no equipos exist', async () => {
    mockGetEquipos.mockResolvedValueOnce([])

    render(<TablaEquipos onEdit={vi.fn()} />, { wrapper })

    const msg = await screen.findByText(/no hay asignaciones/i)
    expect(msg).toBeTruthy()
  })

  it('shows pagination when there are more than 20 equipos', async () => {
    const uid25 = 'cccccccc-0000-0000-0000-000000000099'
    const items = Array.from({ length: 25 }, (_, i) =>
      makeEquipo({
        id: `id-${i}`,
        usuario_id: i === 24 ? uid25 : `dddddddd-0000-0000-0000-${String(i).padStart(12, '0')}`,
        rol: 'PROFESOR',
      }),
    )
    mockGetEquipos.mockResolvedValueOnce(items)

    render(<TablaEquipos onEdit={vi.fn()} />, { wrapper })

    const nextBtn = await screen.findByRole('button', { name: /siguiente/i })
    expect(nextBtn).not.toBeDisabled()

    // Page 1 shows first 20 — uid25 not visible
    expect(screen.queryByText(uid25)).toBeNull()

    fireEvent.click(nextBtn)
    expect(screen.getByText(uid25)).toBeTruthy()
  })
})
