// __tests__/TablaTareas.test.tsx
// TDD tests for TablaTareas — render list, filter by estado.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TablaTareas } from '../components/tareas/TablaTareas'
import type { Tarea } from '../types'

vi.mock('../services/tareasService', () => ({
  getTareas: vi.fn(),
}))

import { getTareas } from '../services/tareasService'
const mockGetTareas = getTareas as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeTarea(overrides: Partial<Tarea> = {}): Tarea {
  return {
    id: crypto.randomUUID(),
    titulo: 'Tarea ejemplo',
    descripcion: null,
    estado: 'Pendiente',
    asignado_a: crypto.randomUUID(),
    asignado_por: crypto.randomUUID(),
    materia_id: null,
    contexto_id: null,
    tenant_id: 'tenant-1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('TablaTareas', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders tarea rows when data is available', async () => {
    mockGetTareas.mockResolvedValueOnce([
      makeTarea({ titulo: 'Revisar planillas' }),
      makeTarea({ titulo: 'Actualizar calendarios' }),
    ])

    render(<TablaTareas onSelect={vi.fn()} />, { wrapper })

    expect(await screen.findByText('Revisar planillas')).toBeTruthy()
    expect(screen.getByText('Actualizar calendarios')).toBeTruthy()
  })

  it('filters tareas by estado when filter is applied', async () => {
    mockGetTareas.mockResolvedValueOnce([
      makeTarea({ titulo: 'Tarea Pendiente', estado: 'Pendiente' }),
      makeTarea({ titulo: 'Tarea Resuelta', estado: 'Resuelta' }),
    ])

    render(<TablaTareas onSelect={vi.fn()} />, { wrapper })

    await screen.findByText('Tarea Pendiente')

    const estadoSelect = screen.getByLabelText(/estado/i)
    fireEvent.change(estadoSelect, { target: { value: 'Resuelta' } })

    expect(screen.queryByText('Tarea Pendiente')).toBeNull()
    expect(screen.getByText('Tarea Resuelta')).toBeTruthy()
  })

  it('shows estado badge for each tarea', async () => {
    mockGetTareas.mockResolvedValueOnce([
      makeTarea({ titulo: 'Tarea En Progreso', estado: 'En_progreso' }),
    ])

    render(<TablaTareas onSelect={vi.fn()} />, { wrapper })

    await screen.findByText('Tarea En Progreso')
    const badges = document.querySelectorAll('span')
    const badge = Array.from(badges).find(
      (el) => el.textContent?.trim() === 'En progreso',
    )
    expect(badge).toBeTruthy()
  })

  it('shows empty state when no tareas', async () => {
    mockGetTareas.mockResolvedValueOnce([])

    render(<TablaTareas onSelect={vi.fn()} />, { wrapper })

    expect(await screen.findByText(/no hay tareas/i)).toBeTruthy()
  })
})
