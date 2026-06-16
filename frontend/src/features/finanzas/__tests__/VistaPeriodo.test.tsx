// __tests__/VistaPeriodo.test.tsx
// TDD tests for VistaPeriodo — renderiza segmentos general/NEXO/facturantes y KPIs.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { VistaPeriodo } from '../components/VistaPeriodo'
import type { VistaPeriodoOut } from '../types'

vi.mock('../services/liquidacionesService', () => ({
  getVistaPeriodo: vi.fn(),
  cerrarPeriodo: vi.fn(),
}))

import { getVistaPeriodo } from '../services/liquidacionesService'
const mockGetVista = getVistaPeriodo as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeVista(overrides: Partial<VistaPeriodoOut> = {}): VistaPeriodoOut {
  return {
    general: [
      {
        id: 'liq-1',
        usuario_id: 'u-1',
        nombre_docente: 'María García',
        rol: 'PROFESOR',
        es_nexo: false,
        es_facturante: false,
        periodo: '2024-03',
        cohorte_id: 'c-1',
        monto_base: 100000,
        monto_plus: 20000,
        monto_total: 120000,
        estado: 'abierta',
        created_at: '2024-03-01T00:00:00Z',
      },
    ],
    nexo: [
      {
        id: 'liq-2',
        usuario_id: 'u-2',
        nombre_docente: 'Carlos NEXO',
        rol: 'NEXO',
        es_nexo: true,
        es_facturante: false,
        periodo: '2024-03',
        cohorte_id: 'c-1',
        monto_base: 50000,
        monto_plus: 0,
        monto_total: 50000,
        estado: 'abierta',
        created_at: '2024-03-01T00:00:00Z',
      },
    ],
    facturantes: [
      {
        id: 'liq-3',
        usuario_id: 'u-3',
        nombre_docente: 'Ana Facturante',
        rol: 'PROFESOR',
        es_nexo: false,
        es_facturante: true,
        periodo: '2024-03',
        cohorte_id: 'c-1',
        monto_base: 80000,
        monto_plus: 10000,
        monto_total: 90000,
        estado: 'abierta',
        created_at: '2024-03-01T00:00:00Z',
      },
    ],
    kpis: {
      total_sin_factura: 170000,
      total_con_factura: 90000,
      cantidad_docentes: 3,
      cantidad_nexos: 1,
    },
    ...overrides,
  }
}

describe('VistaPeriodo', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renderiza los tres segmentos cuando hay datos', async () => {
    mockGetVista.mockResolvedValueOnce(makeVista())

    render(<VistaPeriodo cohorteId="c-1" periodo="2024-03" />, { wrapper })

    expect(await screen.findByText('María García')).toBeTruthy()
    expect(screen.getByText('Carlos NEXO')).toBeTruthy()
    expect(screen.getByText('Ana Facturante')).toBeTruthy()
  })

  it('renderiza los KPIs de total_sin_factura y total_con_factura', async () => {
    mockGetVista.mockResolvedValueOnce(makeVista())

    render(<VistaPeriodo cohorteId="c-1" periodo="2024-03" />, { wrapper })

    const sinFactura = await screen.findByText(/sin factura/i)
    const conFactura = screen.getByText(/con factura/i)
    expect(sinFactura).toBeTruthy()
    expect(conFactura).toBeTruthy()
  })

  it('muestra los títulos de sección General, NEXO y Facturantes', async () => {
    mockGetVista.mockResolvedValueOnce(makeVista())

    render(<VistaPeriodo cohorteId="c-1" periodo="2024-03" />, { wrapper })

    expect(await screen.findByText('General')).toBeTruthy()
    // NEXO appears both as section heading and as rol value in the table — use getAllByText
    const nexoElements = await screen.findAllByText('NEXO')
    expect(nexoElements.length).toBeGreaterThan(0)
    expect(screen.getByText('Facturantes')).toBeTruthy()
  })

  it('muestra mensaje de segmento vacío cuando no hay filas en un segmento', async () => {
    mockGetVista.mockResolvedValueOnce(makeVista({ nexo: [] }))

    render(<VistaPeriodo cohorteId="c-1" periodo="2024-03" />, { wrapper })

    await screen.findByText('General')
    const emptyMsgs = screen.getAllByText(/sin registros/i)
    expect(emptyMsgs.length).toBeGreaterThan(0)
  })

  it('muestra el botón de cerrar período cuando hay liquidaciones abiertas', async () => {
    mockGetVista.mockResolvedValueOnce(makeVista())

    render(<VistaPeriodo cohorteId="c-1" periodo="2024-03" />, { wrapper })

    const btn = await screen.findByRole('button', { name: /cerrar período/i })
    expect(btn).toBeTruthy()
  })
})
