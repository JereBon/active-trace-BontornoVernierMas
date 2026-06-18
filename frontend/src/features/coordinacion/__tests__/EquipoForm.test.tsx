// __tests__/EquipoForm.test.tsx
// TDD tests for EquipoForm — renders selects, validation, submit.

import type { ReactNode } from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { EquipoForm } from '../components/equipos/EquipoForm'

vi.mock('../services/equiposService', () => ({
  getUsuarios: vi.fn().mockResolvedValue([
    { id: '00000000-0000-0000-0000-000000000001', nombre: 'Juan', apellidos: 'Pérez', email: 'juan@test.com' },
  ]),
}))

vi.mock('@/features/admin/services/estructuraService', () => ({
  getCarreras: vi.fn().mockResolvedValue([]),
  getCohortes: vi.fn().mockResolvedValue([]),
  getMaterias: vi.fn().mockResolvedValue([]),
}))

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('EquipoForm', () => {
  it('renders all required fields', async () => {
    render(<EquipoForm onSubmit={vi.fn()} onCancel={vi.fn()} />, { wrapper })

    expect(await screen.findByLabelText(/docente/i)).toBeTruthy()
    expect(screen.getByLabelText(/^rol$/i)).toBeTruthy()
    expect(screen.getByLabelText(/vigencia desde/i)).toBeTruthy()
  })

  it('shows validation error when usuario_id is empty and form is submitted', async () => {
    const onSubmit = vi.fn()
    render(<EquipoForm onSubmit={onSubmit} onCancel={vi.fn()} />, { wrapper })

    await screen.findByLabelText(/docente/i)

    const submitBtn = screen.getByRole('button', { name: /guardar/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/seleccioná un docente/i)).toBeTruthy()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onSubmit with correct payload when form is valid', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<EquipoForm onSubmit={onSubmit} onCancel={vi.fn()} />, { wrapper })

    // Wait for query to resolve and user option to appear
    const option = await screen.findByRole('option', { name: /juan/i })
    expect(option).toBeTruthy()

    await user.selectOptions(screen.getByLabelText(/docente/i), '00000000-0000-0000-0000-000000000001')
    await user.clear(screen.getByLabelText(/vigencia desde/i))
    await user.type(screen.getByLabelText(/vigencia desde/i), '2025-03-01')

    await user.click(screen.getByRole('button', { name: /guardar/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ desde: '2025-03-01', usuario_id: '00000000-0000-0000-0000-000000000001' }),
      )
    })
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const onCancel = vi.fn()
    render(<EquipoForm onSubmit={vi.fn()} onCancel={onCancel} />, { wrapper })

    await screen.findByLabelText(/docente/i)

    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))

    expect(onCancel).toHaveBeenCalledOnce()
  })
})
