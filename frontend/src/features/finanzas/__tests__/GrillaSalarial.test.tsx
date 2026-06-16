// __tests__/GrillaSalarial.test.tsx
// TDD tests for GrillaSalarial — tabla SalarioBase renderiza filas + form de creación.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { GrillaSalarial } from '../components/GrillaSalarial'
import type { SalarioBase, SalarioPlus } from '../types'

vi.mock('../services/grillaService', () => ({
  getSalariosBase: vi.fn(),
  getSalariosPlus: vi.fn(),
  createSalarioBase: vi.fn(),
  createSalarioPlus: vi.fn(),
  updateSalarioBase: vi.fn(),
  updateSalarioPlus: vi.fn(),
}))

import { getSalariosBase, getSalariosPlus } from '../services/grillaService'
const mockGetBase = getSalariosBase as ReturnType<typeof vi.fn>
const mockGetPlus = getSalariosPlus as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeBase(overrides: Partial<SalarioBase> = {}): SalarioBase {
  return {
    id: crypto.randomUUID(),
    rol: 'PROFESOR',
    monto: 100000,
    vigencia_desde: '2024-01-01',
    vigencia_hasta: null,
    tenant_id: 'tenant-1',
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

function makePlus(overrides: Partial<SalarioPlus> = {}): SalarioPlus {
  return {
    id: crypto.randomUUID(),
    grupo: 'MATEMATICA',
    rol: 'PROFESOR',
    monto: 20000,
    vigencia_desde: '2024-01-01',
    vigencia_hasta: null,
    tenant_id: 'tenant-1',
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('GrillaSalarial', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renderiza filas de SalarioBase cuando hay datos', async () => {
    mockGetBase.mockResolvedValueOnce([
      makeBase({ rol: 'PROFESOR', monto: 100000 }),
      makeBase({ rol: 'TUTOR', monto: 80000, id: 'b-2' }),
    ])
    mockGetPlus.mockResolvedValueOnce([])

    render(<GrillaSalarial />, { wrapper })

    expect(await screen.findByText('PROFESOR')).toBeTruthy()
    expect(screen.getByText('TUTOR')).toBeTruthy()
  })

  it('muestra mensaje vacío cuando no hay registros de SalarioBase', async () => {
    mockGetBase.mockResolvedValueOnce([])
    mockGetPlus.mockResolvedValueOnce([])

    render(<GrillaSalarial />, { wrapper })

    const msg = await screen.findByText(/sin registros de salario base/i)
    expect(msg).toBeTruthy()
  })

  it('muestra el formulario de creación de SalarioBase al hacer click en Agregar', async () => {
    mockGetBase.mockResolvedValueOnce([])
    mockGetPlus.mockResolvedValueOnce([])

    render(<GrillaSalarial />, { wrapper })

    await screen.findByText(/sin registros de salario base/i)

    const [btnAgregarBase] = screen.getAllByRole('button', { name: /\+ agregar/i })
    fireEvent.click(btnAgregarBase)

    expect(screen.getByText(/nuevo salariobase/i)).toBeTruthy()
  })

  it('renderiza filas de SalarioPlus con grupo y rol', async () => {
    mockGetBase.mockResolvedValueOnce([])
    mockGetPlus.mockResolvedValueOnce([
      makePlus({ grupo: 'FISICA', rol: 'COORDINADOR', monto: 30000 }),
    ])

    render(<GrillaSalarial />, { wrapper })

    expect(await screen.findByText('FISICA')).toBeTruthy()
    expect(screen.getByText('COORDINADOR')).toBeTruthy()
  })
})
