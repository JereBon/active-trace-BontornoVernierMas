// __tests__/EstructuraAcademica.test.tsx
// TDD tests for EstructuraAcademica — ABM carreras/cohortes/materias incl. categoria_clave.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { EstructuraAcademica } from '../components/EstructuraAcademica'
import type { Carrera, Cohorte, Materia } from '../types'

vi.mock('../services/estructuraService', () => ({
  getCarreras: vi.fn(),
  getCohortes: vi.fn(),
  getMaterias: vi.fn(),
  createCarrera: vi.fn(),
  createCohorte: vi.fn(),
  createMateria: vi.fn(),
  updateCarrera: vi.fn(),
  updateCohorte: vi.fn(),
  updateMateria: vi.fn(),
  deleteCarrera: vi.fn(),
}))

import { getCarreras, getCohortes, getMaterias } from '../services/estructuraService'
const mockGetCarreras = getCarreras as ReturnType<typeof vi.fn>
const mockGetCohortes = getCohortes as ReturnType<typeof vi.fn>
const mockGetMaterias = getMaterias as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function makeCarrera(o: Partial<Carrera> = {}): Carrera {
  return {
    id: crypto.randomUUID(),
    nombre: 'Ingeniería en Sistemas',
    codigo: 'ISI',
    activa: true,
    tenant_id: 't-1',
    created_at: '2024-01-01T00:00:00Z',
    ...o,
  }
}

function makeCohorte(o: Partial<Cohorte> = {}): Cohorte {
  return {
    id: crypto.randomUUID(),
    carrera_id: 'c-1',
    carrera_nombre: 'Ingeniería en Sistemas',
    anio: 2024,
    plan: 'Plan 2023',
    activa: true,
    tenant_id: 't-1',
    created_at: '2024-01-01T00:00:00Z',
    ...o,
  }
}

function makeMateria(o: Partial<Materia> = {}): Materia {
  return {
    id: crypto.randomUUID(),
    nombre: 'Cálculo I',
    codigo: 'MAT101',
    categoria_clave: 'MATEMATICA',
    activa: true,
    tenant_id: 't-1',
    created_at: '2024-01-01T00:00:00Z',
    ...o,
  }
}

describe('EstructuraAcademica', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renderiza carreras cuando hay datos', async () => {
    mockGetCarreras.mockResolvedValueOnce([makeCarrera({ nombre: 'Ingeniería en Sistemas' })])
    mockGetCohortes.mockResolvedValueOnce([])
    mockGetMaterias.mockResolvedValueOnce([])

    render(<EstructuraAcademica />, { wrapper })

    expect(await screen.findByText('Ingeniería en Sistemas')).toBeTruthy()
  })

  it('muestra mensaje vacío cuando no hay carreras', async () => {
    mockGetCarreras.mockResolvedValueOnce([])
    mockGetCohortes.mockResolvedValueOnce([])
    mockGetMaterias.mockResolvedValueOnce([])

    render(<EstructuraAcademica />, { wrapper })

    const msg = await screen.findByText(/sin carreras/i)
    expect(msg).toBeTruthy()
  })

  it('renderiza materias con campo categoria_clave', async () => {
    mockGetCarreras.mockResolvedValueOnce([])
    mockGetCohortes.mockResolvedValueOnce([])
    mockGetMaterias.mockResolvedValueOnce([
      makeMateria({ nombre: 'Álgebra', categoria_clave: 'MATEMATICA' }),
    ])

    render(<EstructuraAcademica />, { wrapper })

    expect(await screen.findByText('Álgebra')).toBeTruthy()
    expect(screen.getByText('MATEMATICA')).toBeTruthy()
  })

  it('muestra el formulario de materia al hacer click en Agregar', async () => {
    mockGetCarreras.mockResolvedValueOnce([])
    mockGetCohortes.mockResolvedValueOnce([])
    mockGetMaterias.mockResolvedValueOnce([])

    render(<EstructuraAcademica />, { wrapper })

    await screen.findByText(/sin materias/i)

    // El botón de Materias es el tercer "Agregar"
    const btns = screen.getAllByRole('button', { name: /\+ agregar/i })
    fireEvent.click(btns[btns.length - 1])

    expect(screen.getByText(/nueva materia/i)).toBeTruthy()
  })

  it('renderiza cohortes con año y plan', async () => {
    mockGetCarreras.mockResolvedValueOnce([])
    mockGetCohortes.mockResolvedValueOnce([makeCohorte({ anio: 2024, plan: 'Plan 2023' })])
    mockGetMaterias.mockResolvedValueOnce([])

    render(<EstructuraAcademica />, { wrapper })

    expect(await screen.findByText('2024')).toBeTruthy()
    expect(screen.getByText('Plan 2023')).toBeTruthy()
  })
})
