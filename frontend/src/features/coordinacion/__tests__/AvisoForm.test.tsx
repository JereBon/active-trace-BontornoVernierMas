// __tests__/AvisoForm.test.tsx
// TDD tests for AvisoForm — validation scope, submit.

import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AvisoForm } from '../components/avisos/AvisoForm'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('AvisoForm', () => {
  it('renders titulo, cuerpo, scope fields', () => {
    render(<AvisoForm onSubmit={vi.fn()} onCancel={vi.fn()} />, { wrapper: Wrapper })

    expect(screen.getByLabelText(/título/i)).toBeTruthy()
    expect(screen.getByLabelText(/cuerpo/i)).toBeTruthy()
    expect(screen.getByLabelText(/alcance/i)).toBeTruthy()
  })

  it('shows validation error when titulo is empty on submit', async () => {
    const onSubmit = vi.fn()
    render(<AvisoForm onSubmit={onSubmit} onCancel={vi.fn()} />, { wrapper: Wrapper })

    fireEvent.click(screen.getByRole('button', { name: /publicar/i }))

    await waitFor(() => {
      expect(screen.getByText(/título es requerido/i)).toBeTruthy()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onSubmit with correct payload when form is valid', async () => {
    const onSubmit = vi.fn()
    render(<AvisoForm onSubmit={onSubmit} onCancel={vi.fn()} />, { wrapper: Wrapper })

    fireEvent.change(screen.getByLabelText(/título/i), {
      target: { value: 'Recordatorio' },
    })
    fireEvent.change(screen.getByLabelText(/cuerpo/i), {
      target: { value: 'Descripción del aviso' },
    })
    fireEvent.change(screen.getByLabelText(/vigencia desde/i), {
      target: { value: '2025-03-01T10:00' },
    })
    fireEvent.change(screen.getByLabelText(/vigencia hasta/i), {
      target: { value: '2025-04-01T10:00' },
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
    render(<AvisoForm onSubmit={vi.fn()} onCancel={onCancel} />, { wrapper: Wrapper })

    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(onCancel).toHaveBeenCalledOnce()
  })
})
