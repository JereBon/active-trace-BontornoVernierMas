// features/comision/components/TablaMonitor.tsx
// Paginated monitor table — shows student activity status.
import { useState } from 'react'
import { Spinner } from '@/shared/components/Spinner'
import { useMonitor } from '../hooks/useMonitor'
import type { MonitorParams } from '../types'

interface Props {
  params: MonitorParams
}

const PAGE_SIZE = 25

export function TablaMonitor({ params }: Props) {
  const { data, isLoading, error } = useMonitor(params)
  const [page, setPage] = useState(0)

  if (isLoading) return <Spinner />
  if (error) return <p className="text-sm text-red-600">{error.message}</p>
  if (!data || data.length === 0)
    return <p className="text-sm text-gray-500">Sin resultados con los filtros actuales.</p>

  const totalPages = Math.ceil(data.length / PAGE_SIZE)
  const pageData = data.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-500">{data.length} resultado{data.length !== 1 ? 's' : ''}</p>
      <div className="overflow-x-auto rounded-md border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3 text-left">Nombre</th>
              <th className="px-4 py-3 text-left">Comisión</th>
              <th className="px-4 py-3 text-right">Aprobadas</th>
              <th className="px-4 py-3 text-right">No aprobadas</th>
              <th className="px-4 py-3 text-right">Faltantes</th>
              <th className="px-4 py-3 text-center">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {pageData.map((item) => (
              <tr key={item.entrada_padron_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">
                  {item.apellidos}, {item.nombre}
                </td>
                <td className="px-4 py-3 text-gray-600">{item.comision ?? '—'}</td>
                <td className="px-4 py-3 text-right text-green-700">{item.cant_aprobadas}</td>
                <td className="px-4 py-3 text-right text-red-600">{item.cant_no_aprobadas}</td>
                <td className="px-4 py-3 text-right text-orange-600">{item.cant_faltantes}</td>
                <td className="px-4 py-3 text-center">
                  {item.es_atrasado ? (
                    <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                      Atrasado
                    </span>
                  ) : (
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                      Al día
                    </span>
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
          <span className="text-sm text-gray-600">{page + 1} / {totalPages}</span>
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
