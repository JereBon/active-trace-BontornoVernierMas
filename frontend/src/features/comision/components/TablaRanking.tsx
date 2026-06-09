// features/comision/components/TablaRanking.tsx
// Ranking sorted by approved activity count descending.
import { Spinner } from '@/shared/components/Spinner'
import { useRanking } from '../hooks/useRanking'

interface Props {
  materiaId: string
}

export function TablaRanking({ materiaId }: Props) {
  const { data, isLoading, error } = useRanking(materiaId)

  if (isLoading) return <Spinner />
  if (error) return <p className="text-sm text-red-600">{error.message}</p>
  if (!data || data.length === 0)
    return <p className="text-sm text-gray-500">No hay datos de ranking disponibles.</p>

  const sorted = [...data].sort((a, b) => b.cant_aprobadas - a.cant_aprobadas)

  return (
    <div className="overflow-x-auto rounded-md border border-gray-200">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
          <tr>
            <th className="px-4 py-3 text-left">#</th>
            <th className="px-4 py-3 text-left">Nombre</th>
            <th className="px-4 py-3 text-left">Comisión</th>
            <th className="px-4 py-3 text-right">Aprobadas</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {sorted.map((item, idx) => (
            <tr key={item.entrada_padron_id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-gray-400">{idx + 1}</td>
              <td className="px-4 py-3 font-medium text-gray-900">
                {item.apellidos}, {item.nombre}
              </td>
              <td className="px-4 py-3 text-gray-600">{item.comision ?? '—'}</td>
              <td className="px-4 py-3 text-right">
                <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                  {item.cant_aprobadas}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
