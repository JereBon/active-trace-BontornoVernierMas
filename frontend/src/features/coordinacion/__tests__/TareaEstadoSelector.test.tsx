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
        estadoActual="pendiente"
        onChange={vi.fn()}
      />,
    )

    const select = screen.getByRole('combobox') as HTMLSelectElement
    expect(select.value).toBe('pendiente')
  })

  it('calls onChange with new estado when selection changes', () => {
    const onChange = vi.fn()
    render(
      <TareaEstadoSelector
        tareaId="t1"
        estadoActual="pendiente"
        onChange={onChange}
      />,
    )

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'completada' } })

    expect(onChange).toHaveBeenCalledWith('completada')
  })

  it('renders all three estado options', () => {
    render(
      <TareaEstadoSelector
        tareaId="t1"
        estadoActual="en_progreso"
        onChange={vi.fn()}
      />,
    )

    const options = screen.getAllByRole('option')
    const values = options.map((o) => (o as HTMLOptionElement).value)
    expect(values).toContain('pendiente')
    expect(values).toContain('en_progreso')
    expect(values).toContain('completada')
  })
})
