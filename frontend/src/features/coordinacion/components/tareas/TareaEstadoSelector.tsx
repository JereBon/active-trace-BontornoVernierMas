// features/coordinacion/components/tareas/TareaEstadoSelector.tsx
import type { TareaEstado } from '../../types'

interface Props {
  tareaId: string
  estadoActual: TareaEstado
  onChange: (nuevoEstado: TareaEstado) => void
  disabled?: boolean
}

const ESTADOS: { value: TareaEstado; label: string }[] = [
  { value: 'Pendiente', label: 'Pendiente' },
  { value: 'En_progreso', label: 'En Progreso' },
  { value: 'Resuelta', label: 'Resuelta' },
  { value: 'Cancelada', label: 'Cancelada' },
]

export function TareaEstadoSelector({ tareaId: _tareaId, estadoActual, onChange, disabled }: Props) {
  return (
    <select
      value={estadoActual}
      onChange={(e) => onChange(e.target.value as TareaEstado)}
      disabled={disabled}
      className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
    >
      {ESTADOS.map(({ value, label }) => (
        <option key={value} value={value}>
          {label}
        </option>
      ))}
    </select>
  )
}
