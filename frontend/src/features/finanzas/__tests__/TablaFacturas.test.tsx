// __tests__/TablaFacturas.test.tsx
// TDD tests for TablaFacturas — tabla con estados + cambio Pendiente→Abonada.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TablaFacturas } from '../components/TablaFacturas'
import type { Factura } from '../types'

vi.mock('../services/facturasService', () => ({
  getFacturas: vi.fn(),
  createFactura: vi.fn(),
  cambiarEstadoFactura: vi.fn(),
}))

import { cambiarEstadoFactura, getFacturas } from '../services/facturasService'
const mockGetFacturas = getFacturas as ReturnType<typeof vi.fn>
const mockCambiarEstado = cambiarEstadoFactura as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeFactura(overrides: Partial<Factura> = {}): Factura {
  return {
    id: crypto.randomUUID(),
    usuario_id: 'u-1',
    nombre_docente: 'Juan Pérez',
    periodo: '2024-03',
    monto: 120000,
    estado: 'pendiente',
    numero: null,
    fecha_emision: null,
    fecha_abono: null,
    tenant_id: 'tenant-1',
    created_at: '2024-03-01T00:00:00Z',
    ...overrides,
  }
}

describe('TablaFacturas', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renderiza filas de facturas con su estado', async () => {
    mockGetFacturas.mockResolvedValueOnce([
      makeFactura({ nombre_docente: 'Juan Pérez', estado: 'pendiente' }),
      makeFactura({ id: 'f-2', nombre_docente: 'Laura Gómez', estado: 'abonada' }),
    ])

    render(<TablaFacturas />, { wrapper })

    expect(await screen.findByText('Juan Pérez')).toBeTruthy()
    expect(screen.getByText('Laura Gómez')).toBeTruthy()
    expect(screen.getByText('pendiente')).toBeTruthy()
    expect(screen.getByText('abonada')).toBeTruthy()
  })

  it('muestra mensaje vacío cuando no hay facturas', async () => {
    mockGetFacturas.mockResolvedValueOnce([])

    render(<TablaFacturas />, { wrapper })

    const msg = await screen.findByText(/no hay facturas/i)
    expect(msg).toBeTruthy()
  })

  it('muestra botón "Marcar abonada" para facturas en estado pendiente', async () => {
    mockGetFacturas.mockResolvedValueOnce([
      makeFactura({ estado: 'pendiente' }),
    ])

    render(<TablaFacturas />, { wrapper })

    const btn = await screen.findByRole('button', { name: /marcar abonada/i })
    expect(btn).toBeTruthy()
  })

  it('no muestra botón de acción para facturas ya abonadas', async () => {
    mockGetFacturas.mockResolvedValueOnce([
      makeFactura({ estado: 'abonada' }),
    ])

    render(<TablaFacturas />, { wrapper })

    await screen.findByText('abonada')
    expect(screen.queryByRole('button', { name: /marcar abonada/i })).toBeNull()
  })

  it('llama a cambiarEstadoFactura al hacer click en "Marcar abonada"', async () => {
    const factura = makeFactura({ id: 'fac-123', estado: 'pendiente' })
    mockGetFacturas.mockResolvedValue([factura])
    mockCambiarEstado.mockResolvedValue({ ...factura, estado: 'abonada' })

    render(<TablaFacturas />, { wrapper })

    const btn = await screen.findByRole('button', { name: /marcar abonada/i })
    fireEvent.click(btn)

    // Give the mutation time to fire
    await new Promise((r) => setTimeout(r, 50))
    expect(mockCambiarEstado).toHaveBeenCalledWith('fac-123', 'abonada')
  })
})
