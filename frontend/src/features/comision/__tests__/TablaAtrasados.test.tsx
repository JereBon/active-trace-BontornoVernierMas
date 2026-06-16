// __tests__/TablaAtrasados.test.tsx
// TDD tests for TablaAtrasados — render with data, empty state, pagination.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TablaAtrasados } from '../components/TablaAtrasados'
import type { AtrasadoItem } from '../types'

vi.mock('../services/analisisService', () => ({
  getAtrasados: vi.fn(),
}))

import { getAtrasados } from '../services/analisisService'
const mockGetAtrasados = getAtrasados as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeAtrasado(overrides: Partial<AtrasadoItem> = {}): AtrasadoItem {
  return {
    entrada_padron_id: crypto.randomUUID(),
    nombre: 'Juan',
    apellidos: 'Pérez',
    comision: '2024-A',
    regional: null,
    actividades_faltantes: ['TP1'],
    actividades_no_aprobadas: [],
    ...overrides,
  }
}

describe('TablaAtrasados', () => {
  beforeEach(() => { vi.clearAllMocks() })

  // RED: renders with data
  it('renders student rows when data is available', async () => {
    mockGetAtrasados.mockResolvedValueOnce([makeAtrasado({ nombre: 'Ana', apellidos: 'García' })])

    render(<TablaAtrasados materiaId="m1" />, { wrapper })

    const row = await screen.findByText(/García, Ana/i)
    expect(row).toBeTruthy()
  })

  // GREEN: empty state when no atrasados
  it('shows empty state when there are no atrasados', async () => {
    mockGetAtrasados.mockResolvedValueOnce([])

    render(<TablaAtrasados materiaId="m1" />, { wrapper })

    const msg = await screen.findByText(/no hay alumnos atrasados/i)
    expect(msg).toBeTruthy()
  })

  // Triangulation: pagination — only PAGE_SIZE rows visible at a time
  it('shows pagination controls when there are more than 20 atrasados', async () => {
    const items = Array.from({ length: 25 }, (_, i) =>
      makeAtrasado({ nombre: `Alumno${i}`, apellidos: 'Test', entrada_padron_id: `id-${i}` }),
    )
    mockGetAtrasados.mockResolvedValueOnce(items)

    render(<TablaAtrasados materiaId="m1" />, { wrapper })

    const nextBtn = await screen.findByRole('button', { name: /siguiente/i })
    expect(nextBtn).not.toBeDisabled()

    // Initially shows 20, not 25
    expect(screen.queryByText(/Alumno24/i)).toBeNull()

    fireEvent.click(nextBtn)
    expect(screen.getByText(/Alumno24/i)).toBeTruthy()
  })
})
