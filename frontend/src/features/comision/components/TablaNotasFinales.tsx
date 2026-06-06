// features/comision/components/TablaNotasFinales.tsx
// Table of final average grades per student.
import { Spinner } from '@/shared/components/Spinner'
import { useNotasFinales } from '../hooks/useNotasFinales'

interface Props {
  materiaId: string
}

export function TablaNotasFinales({ materiaId }: Props) {
  const { data, isLoading, error } = useNotasFinales(materiaId)

  if (isLoading) return <Spinner />
  if (error) return <p className="text-sm text-red-600">{error.message}</p>
  if (!data || data.length === 0)
    return <p className="text-sm text-gray-500">No hay notas finales disponibles.</p>

  return (
    <div className="overflow-x-auto rounded-md border border-gray-200">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
          <tr>
            <th className="px-4 py-3 text-left">Nombre</th>
            <th className="px-4 py-3 text-left">Comisión</th>
            <th className="px-4 py-3 text-right">Nota final</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {data.map((item) => (
            <tr key={item.entrada_padron_id} className="hover:bg-gray-50">
              <td className="px-4 py-3 font-medium text-gray-900">
                {item.apellidos}, {item.nombre}
              </td>
              <td className="px-4 py-3 text-gray-600">{item.comision ?? '—'}</td>
              <td className="px-4 py-3 text-right">
                {item.nota_final !== null ? (
                  <span className="font-semibold text-gray-800">
                    {item.nota_final.toFixed(2)}
                  </span>
                ) : (
                  <span className="text-gray-400">S/N</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
