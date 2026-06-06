// features/coordinacion/components/tareas/TablaTareas.tsx
import { useState } from 'react'
import { useTareas } from '../../hooks/useTareas'
import type { Tarea, TareaEstado, TareaPrioridad } from '../../types'

const PRIORIDAD_CLASS: Record<TareaPrioridad, string> = {
  baja: 'bg-gray-100 text-gray-700',
  media: 'bg-yellow-100 text-yellow-700',
  alta: 'bg-red-100 text-red-700',
}

interface Props {
  onSelect: (tarea: Tarea) => void
}

export function TablaTareas({ onSelect }: Props) {
  const { data: tareas = [], isLoading } = useTareas()
  const [estadoFilter, setEstadoFilter] = useState<TareaEstado | ''>('')

  if (isLoading) {
    return <p className="text-gray-500">Cargando tareas...</p>
  }

  const filteredTareas = estadoFilter
    ? tareas.filter((t) => t.estado === estadoFilter)
    : tareas

  if (filteredTareas.length === 0 && tareas.length === 0) {
    return <p className="text-center text-gray-400 py-8">No hay tareas registradas.</p>
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <label htmlFor="estado-filter" className="text-sm font-medium text-gray-700">
          Estado
        </label>
        <select
          id="estado-filter"
          value={estadoFilter}
          onChange={(e) => setEstadoFilter(e.target.value as TareaEstado | '')}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
          aria-label="Estado"
        >
          <option value="">Todos</option>
          <option value="pendiente">Pendiente</option>
          <option value="en_progreso">En Progreso</option>
          <option value="completada">Completada</option>
        </select>
      </div>

      {filteredTareas.length === 0 ? (
        <p className="text-center text-gray-400 py-4">No hay tareas con ese filtro.</p>
      ) : (
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Título</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Prioridad</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Asignado a</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredTareas.map((tarea) => (
              <tr
                key={tarea.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => onSelect(tarea)}
              >
                <td className="px-4 py-2 font-medium text-gray-900">{tarea.titulo}</td>
                <td className="px-4 py-2 text-gray-600 capitalize">{tarea.estado.replace('_', ' ')}</td>
                <td className="px-4 py-2">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${PRIORIDAD_CLASS[tarea.prioridad]}`}
                  >
                    {tarea.prioridad}
                  </span>
                </td>
                <td className="px-4 py-2 text-gray-600">{tarea.asignado_nombre ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
