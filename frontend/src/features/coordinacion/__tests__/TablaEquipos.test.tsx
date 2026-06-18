// __tests__/TablaEquipos.test.tsx
// TDD tests for TablaEquipos — render with data, empty state, pagination.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TablaEquipos } from '../components/equipos/TablaEquipos'
import type { Asignacion } from '../types'

vi.mock('../services/equiposService', () => ({
  getAsignaciones: vi.fn(),
  deleteAsignacion: vi.fn(),
  getUsuarios: vi.fn().mockResolvedValue([]),
}))

vi.mock('@/features/admin/services/estructuraService', () => ({
  getCarreras: vi.fn().mockResolvedValue([]),
  getCohortes: vi.fn().mockResolvedValue([]),
  getMaterias: vi.fn().mockResolvedValue([]),
}))

import { getAsignaciones } from '../services/equiposService'
const mockGetAsignaciones = getAsignaciones as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeAsignacion(overrides: Partial<Asignacion> = {}): Asignacion {
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

  it('renders asignacion rows when data is available', async () => {
    const uid1 = crypto.randomUUID()
    const uid2 = crypto.randomUUID()
    mockGetAsignaciones.mockResolvedValueOnce([
      makeAsignacion({ usuario_id: uid1, rol: 'PROFESOR' }),
      makeAsignacion({ usuario_id: uid2, rol: 'TUTOR' }),
    ])

    render(<TablaEquipos onEdit={vi.fn()} />, { wrapper })

    const rows = await screen.findAllByText('PROFESOR')
    expect(rows.length).toBeGreaterThanOrEqual(1)
    const tutorRows = await screen.findAllByText('TUTOR')
    expect(tutorRows.length).toBeGreaterThanOrEqual(1)
  })

  it('shows empty state message when no asignaciones exist', async () => {
    mockGetAsignaciones.mockResolvedValueOnce([])

    render(<TablaEquipos onEdit={vi.fn()} />, { wrapper })

    const msg = await screen.findByText(/no hay asignaciones/i)
    expect(msg).toBeTruthy()
  })

  it('shows pagination when there are more than 20 asignaciones', async () => {
    const items = Array.from({ length: 25 }, (_, i) =>
      makeAsignacion({ id: `id-${i}` }),
    )
    mockGetAsignaciones.mockResolvedValueOnce(items)

    render(<TablaEquipos onEdit={vi.fn()} />, { wrapper })

    const nextBtn = await screen.findByRole('button', { name: /siguiente/i })
    expect(nextBtn).not.toBeDisabled()

    fireEvent.click(nextBtn)
    expect(screen.getByText('Página 2 de 2')).toBeTruthy()
  })
})
