// features/coordinacion/components/coloquios/TablaColoquios.tsx
import { useColoquios } from '../../hooks/useColoquios'
import type { ColoquioEstado } from '../../types'

const ESTADO_CLASS: Record<ColoquioEstado, string> = {
  abierta: 'bg-green-100 text-green-800',
  cerrada: 'bg-gray-100 text-gray-700',
  cancelada: 'bg-red-100 text-red-700',
}

export function TablaColoquios() {
  const { data: coloquios = [], isLoading } = useColoquios()

  if (isLoading) return <p className="text-gray-500">Cargando coloquios...</p>

  if (coloquios.length === 0) {
    return <p className="text-center text-gray-400 py-8">No hay convocatorias de coloquio.</p>
  }

  return (
    <table className="min-w-full divide-y divide-gray-200 text-sm">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Materia</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Fecha</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Descripción</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {coloquios.map((c) => (
          <tr key={c.id} className="hover:bg-gray-50">
            <td className="px-4 py-2 text-gray-900">{c.materia_nombre ?? c.materia_id}</td>
            <td className="px-4 py-2 text-gray-600">
              {new Date(c.fecha).toLocaleDateString('es-AR')}
            </td>
            <td className="px-4 py-2">
              <span
                className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${ESTADO_CLASS[c.estado]}`}
              >
                {c.estado}
              </span>
            </td>
            <td className="px-4 py-2 text-gray-600">{c.descripcion ?? '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
