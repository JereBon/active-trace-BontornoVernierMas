import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTareas } from '../../hooks/useTareas'
import { getUsuarios } from '../../services/equiposService'
import { getMaterias } from '@/features/admin/services/estructuraService'
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
  const [materiaFilter, setMateriaFilter] = useState('')
  const [busqueda, setBusqueda] = useState('')

  const { data: usuarios = [] } = useQuery({ queryKey: ['usuarios'], queryFn: getUsuarios })
  const { data: materias = [] } = useQuery({ queryKey: ['materias'], queryFn: getMaterias })

  const userMap = Object.fromEntries(usuarios.map((u) => [u.id, `${u.nombre}${u.apellidos ? ' ' + u.apellidos : ''}`]))
  const materiaMap = Object.fromEntries(materias.map((m) => [m.id, m.nombre]))

  if (isLoading) {
    return <p className="text-gray-500">Cargando tareas...</p>
  }

  const filteredTareas = tareas.filter((t) => {
    if (estadoFilter && t.estado !== estadoFilter) return false
    if (materiaFilter && t.materia_id !== materiaFilter) return false
    if (busqueda) {
      const q = busqueda.toLowerCase()
      if (
        !t.titulo.toLowerCase().includes(q) &&
        !(t.asignado_nombre ?? '').toLowerCase().includes(q)
      ) return false
    }
    return true
  })

  if (filteredTareas.length === 0 && tareas.length === 0) {
    return <p className="text-center text-gray-400 py-8">No hay tareas registradas.</p>
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="Buscar por título o docente…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1 text-sm w-56"
        />
        <label htmlFor="estado-filter" className="text-sm font-medium text-gray-700">Estado</label>
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
        <label htmlFor="materia-filter" className="text-sm font-medium text-gray-700">Materia</label>
        <select
          id="materia-filter"
          value={materiaFilter}
          onChange={(e) => setMateriaFilter(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
        >
          <option value="">Todas</option>
          {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
        </select>
      </div>

      {filteredTareas.length === 0 ? (
        <p className="text-center text-gray-400 py-4">No hay tareas con ese filtro.</p>
      ) : (
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Título</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Descripción</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Prioridad</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Asignado a</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Creado por</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Materia</th>
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
                <td className="px-4 py-2 text-gray-500 text-xs max-w-xs truncate">
                  {tarea.descripcion ?? '—'}
                </td>
                <td className="px-4 py-2 text-gray-600 capitalize">{tarea.estado.replace('_', ' ')}</td>
                <td className="px-4 py-2">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${PRIORIDAD_CLASS[tarea.prioridad]}`}
                  >
                    {tarea.prioridad}
                  </span>
                </td>
                <td className="px-4 py-2 text-gray-600">{tarea.asignado_nombre ?? '—'}</td>
                <td className="px-4 py-2 text-gray-600">
                  {tarea.asignado_por ? (userMap[tarea.asignado_por] ?? <span className="text-gray-400 text-xs">{tarea.asignado_por.slice(0, 8)}…</span>) : '—'}
                </td>
                <td className="px-4 py-2 text-gray-600">
                  {tarea.materia_id ? (materiaMap[tarea.materia_id] ?? '—') : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
