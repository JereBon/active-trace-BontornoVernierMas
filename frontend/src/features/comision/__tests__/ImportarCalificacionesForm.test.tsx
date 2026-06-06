// __tests__/ImportarCalificacionesForm.test.tsx
// TDD tests for ImportarCalificacionesForm.
// Requires: vitest, @testing-library/react, @testing-library/user-event, msw
//
// To run: add vitest + @testing-library/react to devDependencies and run `npx vitest`.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ImportarCalificacionesForm } from '../components/ImportarCalificacionesForm'

// Mock the service layer — no real HTTP calls in unit tests
vi.mock('../services/calificacionesService', () => ({
  previewCalificaciones: vi.fn(),
}))

import { previewCalificaciones } from '../services/calificacionesService'

const mockPreview = previewCalificaciones as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('ImportarCalificacionesForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // RED test 1: initial render — no preview data, button disabled
  it('renders without data initially and preview button is disabled', () => {
    const onPreview = vi.fn()
    render(<ImportarCalificacionesForm materiaId="mat-1" onPreview={onPreview} />, {
      wrapper,
    })

    expect(screen.getByRole('button', { name: /vista previa/i })).toBeDisabled()
    expect(onPreview).not.toHaveBeenCalled()
  })

  // GREEN + triangulation: preview succeeded with activities
  it('calls onPreview with data when file is selected and preview succeeds', async () => {
    const previewData = {
      actividades_numericas: ['TP1 (Real)', 'TP2 (Real)'],
      actividades_textuales: ['Presentación'],
      alumnos_preview: [],
    }
    mockPreview.mockResolvedValueOnce(previewData)

    const onPreview = vi.fn()
    render(<ImportarCalificacionesForm materiaId="mat-1" onPreview={onPreview} />, {
      wrapper,
    })

    const input = screen.getByTestId('file-input')
    const file = new File(['header\ndata'], 'grades.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    fireEvent.change(input, { target: { files: [file] } })

    const btn = screen.getByRole('button', { name: /vista previa/i })
    expect(btn).not.toBeDisabled()
    fireEvent.click(btn)

    await waitFor(() => {
      expect(mockPreview).toHaveBeenCalledWith('mat-1', file)
      expect(onPreview).toHaveBeenCalledWith(previewData, file)
    })
  })

  // Triangulation: 422 error shows error message
  it('shows error message when preview returns 422', async () => {
    mockPreview.mockRejectedValueOnce(new Error('Columna Email address requerida'))

    const onPreview = vi.fn()
    render(<ImportarCalificacionesForm materiaId="mat-1" onPreview={onPreview} />, {
      wrapper,
    })

    const input = screen.getByTestId('file-input')
    const file = new File(['bad'], 'bad.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /vista previa/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Columna Email address requerida')
      expect(onPreview).not.toHaveBeenCalled()
    })
  })
})
