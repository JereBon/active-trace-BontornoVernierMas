// __tests__/TareaEstadoSelector.test.tsx
// TDD tests for TareaEstadoSelector — render current estado, change calls hook.

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { TareaEstadoSelector } from '../components/tareas/TareaEstadoSelector'

describe('TareaEstadoSelector', () => {
  it('renders select with current estado pre-selected', () => {
    render(
      <TareaEstadoSelector
        tareaId="t1"
        estadoActual="Pendiente"
        onChange={vi.fn()}
      />,
    )

    const select = screen.getByRole('combobox') as HTMLSelectElement
    expect(select.value).toBe('Pendiente')
  })

  it('calls onChange with new estado when selection changes', () => {
    const onChange = vi.fn()
    render(
      <TareaEstadoSelector
        tareaId="t1"
        estadoActual="Pendiente"
        onChange={onChange}
      />,
    )

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'En_progreso' } })

    expect(onChange).toHaveBeenCalledWith('En_progreso')
  })

  it('renders all four estado options', () => {
    render(
      <TareaEstadoSelector
        tareaId="t1"
        estadoActual="En_progreso"
        onChange={vi.fn()}
      />,
    )

    const options = screen.getAllByRole('option')
    const values = options.map((o) => (o as HTMLOptionElement).value)
    expect(values).toContain('Pendiente')
    expect(values).toContain('En_progreso')
    expect(values).toContain('Resuelta')
    expect(values).toContain('Cancelada')
  })
})
