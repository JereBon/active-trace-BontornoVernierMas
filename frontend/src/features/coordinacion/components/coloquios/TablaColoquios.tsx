// features/coordinacion/components/coloquios/TablaColoquios.tsx
// Aligned with backend EvaluacionOut schema
import { useColoquios } from '../../hooks/useColoquios'
import type { EstadoEvaluacion } from '../../types'

const ESTADO_CLASS: Record<EstadoEvaluacion, string> = {
  Abierta: 'bg-green-100 text-green-800',
  Cerrada: 'bg-gray-100 text-gray-700',
  Cancelada: 'bg-red-100 text-red-700',
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
          <th className="px-4 py-2 text-left font-medium text-gray-600">Cohorte</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Tipo</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Instancia</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Días</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Cupos</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {coloquios.map((c) => (
          <tr key={c.id} className="hover:bg-gray-50">
            <td className="px-4 py-2 text-gray-900 font-mono text-xs">{c.materia_id.slice(0, 8)}…</td>
            <td className="px-4 py-2 text-gray-600 font-mono text-xs">{c.cohorte_id.slice(0, 8)}…</td>
            <td className="px-4 py-2 text-gray-600">{c.tipo}</td>
            <td className="px-4 py-2 text-gray-900 font-medium">{c.instancia}</td>
            <td className="px-4 py-2 text-gray-600">{c.dias_disponibles}</td>
            <td className="px-4 py-2 text-gray-600">{c.cupos_disponibles}</td>
            <td className="px-4 py-2">
              <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${ESTADO_CLASS[c.estado as EstadoEvaluacion] ?? ''}`}>
                {c.estado}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
