// __tests__/AvisoForm.test.tsx
// TDD tests for AvisoForm — validation scope, severidad, submit.

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AvisoForm } from '../components/avisos/AvisoForm'

describe('AvisoForm', () => {
  it('renders titulo, cuerpo, scope, severidad fields', () => {
    render(<AvisoForm onSubmit={vi.fn()} onCancel={vi.fn()} />)

    expect(screen.getByLabelText(/título/i)).toBeTruthy()
    expect(screen.getByLabelText(/cuerpo/i)).toBeTruthy()
    expect(screen.getByLabelText(/scope/i)).toBeTruthy()
    expect(screen.getByLabelText(/severidad/i)).toBeTruthy()
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

    fireEvent.click(screen.getByRole('button', { name: /publicar/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          titulo: 'Recordatorio',
          cuerpo: 'Descripción del aviso',
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
