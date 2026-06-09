// features/coordinacion/components/encuentros/TablaEncuentros.tsx
import { useEncuentros } from '../../hooks/useEncuentros'

export function TablaEncuentros() {
  const { data: encuentros = [], isLoading } = useEncuentros()

  if (isLoading) return <p className="text-gray-500">Cargando encuentros...</p>

  if (encuentros.length === 0) {
    return <p className="text-center text-gray-400 py-8">No hay encuentros programados.</p>
  }

  return (
    <table className="min-w-full divide-y divide-gray-200 text-sm">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Fecha</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Hora</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Título</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Meet</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {encuentros.map((e) => (
          <tr key={e.id} className="hover:bg-gray-50">
            <td className="px-4 py-2 text-gray-900">
              {new Date(e.fecha).toLocaleDateString('es-AR')}
            </td>
            <td className="px-4 py-2 text-gray-600">{e.hora}</td>
            <td className="px-4 py-2 text-gray-900">{e.titulo}</td>
            <td className="px-4 py-2 capitalize text-gray-600">{e.estado}</td>
            <td className="px-4 py-2">
              {e.meet_url
                ? <a href={e.meet_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs">Unirse</a>
                : <span className="text-gray-400">—</span>
              }
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
