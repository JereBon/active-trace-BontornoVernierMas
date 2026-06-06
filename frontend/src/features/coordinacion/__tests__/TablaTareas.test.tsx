// __tests__/TablaTareas.test.tsx
// TDD tests for TablaTareas — render list, filter by estado, badge de prioridad.

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
    estado: 'pendiente',
    prioridad: 'media',
    asignado_a: null,
    asignado_nombre: null,
    creado_por: 'user-1',
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
      makeTarea({ titulo: 'Tarea Pendiente', estado: 'pendiente' }),
      makeTarea({ titulo: 'Tarea Completada', estado: 'completada' }),
    ])

    render(<TablaTareas onSelect={vi.fn()} />, { wrapper })

    await screen.findByText('Tarea Pendiente')

    // Select filter "completada"
    const estadoSelect = screen.getByLabelText(/estado/i)
    fireEvent.change(estadoSelect, { target: { value: 'completada' } })

    expect(screen.queryByText('Tarea Pendiente')).toBeNull()
    expect(screen.getByText('Tarea Completada')).toBeTruthy()
  })

  it('shows priority badge for each tarea', async () => {
    mockGetTareas.mockResolvedValueOnce([
      makeTarea({ titulo: 'Tarea Urgente', prioridad: 'alta' }),
    ])

    render(<TablaTareas onSelect={vi.fn()} />, { wrapper })

    await screen.findByText('Tarea Urgente')
    // The badge renders the prioridad text in a styled span
    const badges = document.querySelectorAll('span')
    const altaBadge = Array.from(badges).find(
      (el) => el.textContent?.trim() === 'alta',
    )
    expect(altaBadge).toBeTruthy()
  })

  it('shows empty state when no tareas', async () => {
    mockGetTareas.mockResolvedValueOnce([])

    render(<TablaTareas onSelect={vi.fn()} />, { wrapper })

    expect(await screen.findByText(/no hay tareas/i)).toBeTruthy()
  })
})
