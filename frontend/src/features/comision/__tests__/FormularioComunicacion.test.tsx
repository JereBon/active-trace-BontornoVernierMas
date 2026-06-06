// __tests__/FormularioComunicacion.test.tsx
// TDD tests for FormularioComunicacion — validation, preview, send.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FormularioComunicacion } from '../components/FormularioComunicacion'

vi.mock('../services/comunicacionesService', () => ({
  previewComunicacion: vi.fn(),
  encolarComunicaciones: vi.fn(),
}))

import { previewComunicacion, encolarComunicaciones } from '../services/comunicacionesService'
const mockPreview = previewComunicacion as ReturnType<typeof vi.fn>
const mockEncolar = encolarComunicaciones as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const destinatarios = [{ email: 'alumno@test.invalid', variables: { nombre: 'Test' } }]

describe('FormularioComunicacion', () => {
  beforeEach(() => { vi.clearAllMocks() })

  // RED: submit with empty fields shows validation errors
  it('shows validation errors when fields are empty on submit', async () => {
    render(
      <FormularioComunicacion materiaId="m1" destinatarios={destinatarios} onEnviado={vi.fn()} />,
      { wrapper },
    )

    fireEvent.click(screen.getByRole('button', { name: /enviar/i }))

    await waitFor(() => {
      const alerts = screen.getAllByRole('alert')
      expect(alerts.length).toBeGreaterThanOrEqual(1)
    })
  })

  // GREEN: preview button calls previewComunicacion
  it('calls previewComunicacion when preview button is clicked with filled fields', async () => {
    mockPreview.mockResolvedValueOnce({ asunto: 'Hola Test', cuerpo: 'Cuerpo renderizado' })

    render(
      <FormularioComunicacion materiaId="m1" destinatarios={destinatarios} onEnviado={vi.fn()} />,
      { wrapper },
    )

    fireEvent.change(screen.getByLabelText(/asunto/i), { target: { value: 'Hola {{nombre}}' } })
    fireEvent.change(screen.getByLabelText(/cuerpo/i), { target: { value: 'Estimado {{nombre}}' } })

    fireEvent.click(screen.getByRole('button', { name: /vista previa/i }))

    await waitFor(() => {
      expect(mockPreview).toHaveBeenCalledWith({
        asunto: 'Hola {{nombre}}',
        cuerpo: 'Estimado {{nombre}}',
      })
    })
  })

  // Triangulation: backend error on preview shows inline error
  it('shows server error message when previewComunicacion fails', async () => {
    mockPreview.mockRejectedValueOnce(new Error('Missing template variables: apellidos'))

    render(
      <FormularioComunicacion materiaId="m1" destinatarios={destinatarios} onEnviado={vi.fn()} />,
      { wrapper },
    )

    fireEvent.change(screen.getByLabelText(/asunto/i), { target: { value: 'Hola' } })
    fireEvent.change(screen.getByLabelText(/cuerpo/i), { target: { value: 'Estimado {{apellidos}}' } })
    fireEvent.click(screen.getByRole('button', { name: /vista previa/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Missing template variables/i)
    })
  })
})
