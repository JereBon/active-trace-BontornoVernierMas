// __tests__/ActividadesSelector.test.tsx
// TDD tests for ActividadesSelector.

import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ActividadesSelector } from '../components/ActividadesSelector'

vi.mock('../services/calificacionesService', () => ({
  importarCalificaciones: vi.fn(),
}))

import { importarCalificaciones } from '../services/calificacionesService'
const mockImportar = importarCalificaciones as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const basePreview = {
  actividades_numericas: ['TP1 (Real)', 'TP2 (Real)'],
  actividades_textuales: ['Presentación'],
  alumnos_preview: [],
}

const file = new File(['data'], 'grades.xlsx')

describe('ActividadesSelector', () => {
  beforeEach(() => { vi.clearAllMocks() })

  // RED: all checkboxes rendered and enabled
  it('renders all activities as checked by default', () => {
    render(
      <ActividadesSelector
        materiaId="m1"
        asignacionId="a1"
        file={file}
        preview={basePreview}
        onImportado={vi.fn()}
      />,
      { wrapper },
    )
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes).toHaveLength(3)
    checkboxes.forEach((cb) => expect(cb).toBeChecked())
  })

  // GREEN: validation error when no activity is selected
  it('shows validation error when all activities are unchecked and user confirms', async () => {
    render(
      <ActividadesSelector
        materiaId="m1"
        asignacionId="a1"
        file={file}
        preview={basePreview}
        onImportado={vi.fn()}
      />,
      { wrapper },
    )

    // Uncheck all
    screen.getAllByRole('checkbox').forEach((cb) => fireEvent.click(cb))

    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }))
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/al menos una/i)
    })
  })

  // Triangulation: selected activities are sent on confirm
  it('calls importarCalificaciones with selected activities on confirm', async () => {
    const importResult = { calificaciones_importadas: 5, mensaje: 'Ok' }
    mockImportar.mockResolvedValueOnce(importResult)
    const onImportado = vi.fn()

    render(
      <ActividadesSelector
        materiaId="m1"
        asignacionId="a1"
        file={file}
        preview={basePreview}
        onImportado={onImportado}
      />,
      { wrapper },
    )

    // Uncheck the textual one
    const checkboxes = screen.getAllByRole('checkbox')
    fireEvent.click(checkboxes[2]) // "Presentación"

    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }))

    await waitFor(() => {
      expect(mockImportar).toHaveBeenCalledWith(
        'm1',
        'a1',
        file,
        expect.arrayContaining(['TP1 (Real)', 'TP2 (Real)']),
      )
      expect(onImportado).toHaveBeenCalledWith(importResult)
    })
  })
})
