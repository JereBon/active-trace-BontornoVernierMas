// features/comision/components/TablaAtrasados.tsx
// Client-side paginated table of atrasados.
import { useState } from 'react'
import { Spinner } from '@/shared/components/Spinner'
import { useAtrasados } from '../hooks/useAtrasados'

const PAGE_SIZE = 20

interface Props {
  materiaId: string
}

export function TablaAtrasados({ materiaId }: Props) {
  const { data, isLoading, error } = useAtrasados(materiaId)
  const [page, setPage] = useState(0)

  if (isLoading) return <Spinner />
  if (error) return <p className="text-sm text-red-600">{error.message}</p>
  if (!data || data.length === 0)
    return <p className="text-sm text-gray-500">No hay alumnos atrasados.</p>

  const totalPages = Math.ceil(data.length / PAGE_SIZE)
  const pageData = data.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-500">
        {data.length} alumno{data.length !== 1 ? 's' : ''} atrasado{data.length !== 1 ? 's' : ''}
      </p>
      <div className="overflow-x-auto rounded-md border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3 text-left">Nombre</th>
              <th className="px-4 py-3 text-left">Comisión</th>
              <th className="px-4 py-3 text-left">Act. faltantes</th>
              <th className="px-4 py-3 text-left">Act. no aprobadas</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {pageData.map((item) => (
              <tr key={item.entrada_padron_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">
                  {item.apellidos}, {item.nombre}
                </td>
                <td className="px-4 py-3 text-gray-600">{item.comision ?? '—'}</td>
                <td className="px-4 py-3">
                  {item.actividades_faltantes.length > 0 ? (
                    <span className="inline-flex items-center rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
                      {item.actividades_faltantes.length}
                    </span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {item.actividades_no_aprobadas.length > 0 ? (
                    <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                      {item.actividades_no_aprobadas.length}
                    </span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="rounded border px-3 py-1 text-sm disabled:opacity-40"
          >
            Anterior
          </button>
          <span className="text-sm text-gray-600">
            {page + 1} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
            className="rounded border px-3 py-1 text-sm disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  )
}
