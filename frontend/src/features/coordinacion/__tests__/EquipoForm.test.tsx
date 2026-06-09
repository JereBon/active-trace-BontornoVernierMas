// __tests__/EquipoForm.test.tsx
// TDD tests for EquipoForm — empty render, Zod validation, submit.

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { EquipoForm } from '../components/equipos/EquipoForm'

describe('EquipoForm', () => {
  it('renders all required fields', () => {
    render(<EquipoForm onSubmit={vi.fn()} onCancel={vi.fn()} />)

    expect(screen.getByLabelText(/nombre/i)).toBeTruthy()
    expect(screen.getByLabelText(/descripci/i)).toBeTruthy()
  })

  it('shows validation error when nombre is empty and form is submitted', async () => {
    const onSubmit = vi.fn()
    render(<EquipoForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    const submitBtn = screen.getByRole('button', { name: /guardar/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/nombre es requerido/i)).toBeTruthy()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onSubmit with form data when valid', async () => {
    const onSubmit = vi.fn()
    render(<EquipoForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    fireEvent.change(screen.getByLabelText(/nombre/i), {
      target: { value: 'Equipo Test' },
    })

    const submitBtn = screen.getByRole('button', { name: /guardar/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ nombre: 'Equipo Test' }),
      )
    })
  })

  it('calls onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn()
    render(<EquipoForm onSubmit={vi.fn()} onCancel={onCancel} />)

    const cancelBtn = screen.getByRole('button', { name: /cancelar/i })
    fireEvent.click(cancelBtn)

    expect(onCancel).toHaveBeenCalledOnce()
  })
})
