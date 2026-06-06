// __tests__/UmbralForm.test.tsx
// TDD tests for UmbralForm — Zod validation and submit.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { UmbralForm } from '../components/UmbralForm'

vi.mock('../services/calificacionesService', () => ({
  configurarUmbral: vi.fn(),
}))

import { configurarUmbral } from '../services/calificacionesService'
const mockConfigurar = configurarUmbral as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('UmbralForm', () => {
  beforeEach(() => { vi.clearAllMocks() })

  // RED: empty umbral shows Zod error
  it('shows validation error when umbral_pct is out of range (>100)', async () => {
    render(<UmbralForm materiaId="m1" asignacionId="a1" />, { wrapper })
    const input = screen.getByLabelText(/umbral de aprobación/i)
    fireEvent.change(input, { target: { value: '150' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar/i }))
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/100/i)
    })
  })

  // GREEN: valid submit triggers configurarUmbral
  it('calls configurarUmbral with correct values on valid submit', async () => {
    const umbralResult = { id: 'u1', asignacion_id: 'a1', materia_id: 'm1', umbral_pct: 70, valores_aprobatorios: [] }
    mockConfigurar.mockResolvedValueOnce(umbralResult)
    const onGuardado = vi.fn()

    render(<UmbralForm materiaId="m1" asignacionId="a1" onGuardado={onGuardado} />, { wrapper })
    const input = screen.getByLabelText(/umbral de aprobación/i)
    fireEvent.change(input, { target: { value: '70' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar/i }))

    await waitFor(() => {
      expect(mockConfigurar).toHaveBeenCalledWith('m1', {
        asignacion_id: 'a1',
        umbral_pct: 70,
        valores_aprobatorios: [],
      })
      expect(onGuardado).toHaveBeenCalledWith(umbralResult)
    })
  })

  // Triangulation: umbral below 0 also fails
  it('shows validation error when umbral_pct is negative', async () => {
    render(<UmbralForm materiaId="m1" asignacionId="a1" />, { wrapper })
    fireEvent.change(screen.getByLabelText(/umbral de aprobación/i), { target: { value: '-5' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar/i }))
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/0/i)
    })
  })
})
