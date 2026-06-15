// __tests__/EquipoForm.test.tsx
// TDD tests for EquipoForm — empty render, Zod validation, submit.

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { EquipoForm } from '../components/equipos/EquipoForm'

describe('EquipoForm', () => {
  it('renders all required fields', () => {
    render(<EquipoForm onSubmit={vi.fn()} onCancel={vi.fn()} />)

    expect(screen.getByLabelText(/usuario id/i)).toBeTruthy()
    expect(screen.getByLabelText(/^rol/i)).toBeTruthy()
    expect(screen.getByLabelText(/desde/i)).toBeTruthy()
  })

  it('shows validation error when usuario_id is not a valid UUID', async () => {
    const onSubmit = vi.fn()
    render(<EquipoForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    // Leave usuario_id empty — should fail UUID validation
    const submitBtn = screen.getByRole('button', { name: /guardar/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/uuid válido/i)).toBeTruthy()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onSubmit with form data when valid', async () => {
    const onSubmit = vi.fn()
    render(<EquipoForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    const validUUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
    fireEvent.change(screen.getByLabelText(/usuario id/i), {
      target: { value: validUUID },
    })
    fireEvent.change(screen.getByLabelText(/desde/i), {
      target: { value: '2024-03-01' },
    })

    const submitBtn = screen.getByRole('button', { name: /guardar/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ usuario_id: validUUID }),
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
