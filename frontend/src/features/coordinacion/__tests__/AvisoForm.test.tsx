// __tests__/AvisoForm.test.tsx
// TDD tests for AvisoForm — validation scope, vig_desde/hasta, submit.

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AvisoForm } from '../components/avisos/AvisoForm'

describe('AvisoForm', () => {
  it('renders titulo, cuerpo, scope fields', () => {
    render(<AvisoForm onSubmit={vi.fn()} onCancel={vi.fn()} />)

    expect(screen.getByLabelText(/título/i)).toBeTruthy()
    expect(screen.getByLabelText(/cuerpo/i)).toBeTruthy()
    expect(screen.getByLabelText(/audiencia/i)).toBeTruthy()
  })

  it('shows validation error when titulo is empty on submit', async () => {
    const onSubmit = vi.fn()
    render(<AvisoForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: /publicar/i }))

    await waitFor(() => {
      expect(screen.getByText(/título es requerido/i)).toBeTruthy()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onSubmit with correct payload when form is valid', async () => {
    const onSubmit = vi.fn()
    render(<AvisoForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    fireEvent.change(screen.getByLabelText(/título/i), {
      target: { value: 'Recordatorio' },
    })
    fireEvent.change(screen.getByLabelText(/cuerpo/i), {
      target: { value: 'Descripción del aviso' },
    })
    fireEvent.change(screen.getByLabelText(/vigente desde/i), {
      target: { value: '2024-06-01T08:00' },
    })
    fireEvent.change(screen.getByLabelText(/vigente hasta/i), {
      target: { value: '2024-12-31T23:59' },
    })

    fireEvent.click(screen.getByRole('button', { name: /publicar/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          titulo: 'Recordatorio',
          cuerpo: 'Descripción del aviso',
          vig_desde: new Date('2024-06-01T08:00').toISOString(),
          vig_hasta: new Date('2024-12-31T23:59').toISOString(),
        }),
      )
    })
  })

  it('calls onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn()
    render(<AvisoForm onSubmit={vi.fn()} onCancel={onCancel} />)

    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(onCancel).toHaveBeenCalledOnce()
  })
})
