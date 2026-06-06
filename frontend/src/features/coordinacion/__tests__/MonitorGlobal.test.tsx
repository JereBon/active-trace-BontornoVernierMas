// __tests__/MonitorGlobal.test.tsx
// TDD tests for MonitorGlobalPanel — render without materia filter, apply filters.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MonitorGlobalPanel } from '../components/monitor/MonitorGlobalPanel'
import type { MonitorItem } from '@/features/comision/types'

vi.mock('../services/monitorService', () => ({
  getMonitorGlobal: vi.fn(),
}))

import { getMonitorGlobal } from '../services/monitorService'
const mockGetMonitorGlobal = getMonitorGlobal as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeMonitorItem(overrides: Partial<MonitorItem> = {}): MonitorItem {
  return {
    entrada_padron_id: crypto.randomUUID(),
    nombre: 'Juan',
    apellidos: 'Pérez',
    comision: 'A',
    regional: null,
    materia_id: 'mat-1',
    cant_actividades: 5,
    cant_aprobadas: 3,
    cant_no_aprobadas: 1,
    cant_faltantes: 1,
    es_atrasado: false,
    ...overrides,
  }
}

describe('MonitorGlobalPanel', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders monitor items in a table without materia_id filter', async () => {
    mockGetMonitorGlobal.mockResolvedValueOnce([
      makeMonitorItem({ nombre: 'Ana', apellidos: 'García' }),
      makeMonitorItem({ nombre: 'Luis', apellidos: 'Torres' }),
    ])

    render(<MonitorGlobalPanel />, { wrapper })

    expect(await screen.findByText(/García/i)).toBeTruthy()
    expect(screen.getByText(/Torres/i)).toBeTruthy()
  })

  it('shows empty state when no monitor items', async () => {
    mockGetMonitorGlobal.mockResolvedValueOnce([])

    render(<MonitorGlobalPanel />, { wrapper })

    expect(await screen.findByText(/no hay datos/i)).toBeTruthy()
  })

  it('re-fetches with comision filter when filter input changes', async () => {
    mockGetMonitorGlobal
      .mockResolvedValueOnce([makeMonitorItem({ comision: 'A', apellidos: 'García' })])
      .mockResolvedValueOnce([makeMonitorItem({ comision: 'B', apellidos: 'López' })])

    render(<MonitorGlobalPanel />, { wrapper })

    await screen.findByText(/García/i)

    const comisionInput = screen.getByPlaceholderText(/filtrar comisión/i)
    fireEvent.change(comisionInput, { target: { value: 'B' } })

    await waitFor(() => {
      expect(mockGetMonitorGlobal).toHaveBeenCalledWith(
        expect.objectContaining({ comision: 'B' }),
      )
    })
  })
})
