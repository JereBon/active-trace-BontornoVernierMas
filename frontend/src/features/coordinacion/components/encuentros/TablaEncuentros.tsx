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
          <th className="px-4 py-2 text-left font-medium text-gray-600">Tipo</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Cupo</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {encuentros.map((e) => (
          <tr key={e.id} className="hover:bg-gray-50">
            <td className="px-4 py-2 text-gray-900">
              {new Date(e.fecha).toLocaleDateString('es-AR')}
            </td>
            <td className="px-4 py-2 text-gray-600 capitalize">{e.tipo}</td>
            <td className="px-4 py-2 text-gray-600">{e.cupo_maximo ?? 'Sin límite'}</td>
            <td className="px-4 py-2 text-gray-600 capitalize">{e.estado}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
