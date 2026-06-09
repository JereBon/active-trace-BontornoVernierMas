// __tests__/TablaSinCorregir.test.tsx
// TDD tests for TablaSinCorregir — render with data, CSV button state, export.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TablaSinCorregir } from '../components/TablaSinCorregir'

vi.mock('../services/analisisService', () => ({
  getSinCorregir: vi.fn(),
}))

import { getSinCorregir } from '../services/analisisService'
const mockGetSinCorregir = getSinCorregir as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('TablaSinCorregir', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Stub URL API for Blob export test
    global.URL.createObjectURL = vi.fn(() => 'blob:test')
    global.URL.revokeObjectURL = vi.fn()
  })

  // RED: renders with data
  it('renders rows when sin-corregir data is available', async () => {
    mockGetSinCorregir.mockResolvedValueOnce([
      {
        entrada_padron_id: 'ep1',
        nombre: 'Laura',
        apellidos: 'Torres',
        comision: 'C1',
        actividad: 'TP Final',
        importado_at: '2024-10-01T12:00:00',
      },
    ])

    render(<TablaSinCorregir materiaId="m1" />, { wrapper })
    const row = await screen.findByText(/Torres, Laura/i)
    expect(row).toBeTruthy()
  })

  // GREEN: CSV button is enabled when data exists
  it('enables the export CSV button when there are items', async () => {
    mockGetSinCorregir.mockResolvedValueOnce([
      {
        entrada_padron_id: 'ep1',
        nombre: 'Laura',
        apellidos: 'Torres',
        comision: 'C1',
        actividad: 'TP Final',
        importado_at: '2024-10-01T12:00:00',
      },
    ])

    render(<TablaSinCorregir materiaId="m1" />, { wrapper })
    const btn = await screen.findByTestId('export-csv-btn')
    expect(btn).not.toBeDisabled()
  })

  // Triangulation: clicking export creates a Blob URL
  it('calls URL.createObjectURL when export button is clicked', async () => {
    const mockClick = vi.fn()
    const origCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: string, ...rest: []) => {
      if (tag === 'a') return { href: '', download: '', click: mockClick } as unknown as HTMLAnchorElement
      return origCreate(tag, ...rest)
    })

    mockGetSinCorregir.mockResolvedValueOnce([
      {
        entrada_padron_id: 'ep1',
        nombre: 'Laura',
        apellidos: 'Torres',
        comision: 'C1',
        actividad: 'TP Final',
        importado_at: '2024-10-01T12:00:00',
      },
    ])

    render(<TablaSinCorregir materiaId="m1" />, { wrapper })
    const btn = await screen.findByTestId('export-csv-btn')
    fireEvent.click(btn)

    expect(global.URL.createObjectURL).toHaveBeenCalledWith(expect.any(Blob))
    expect(mockClick).toHaveBeenCalled()
  })
})
