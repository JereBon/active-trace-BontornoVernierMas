// features/finanzas/pages/HistorialPage.tsx
import { useState } from 'react'
import { useHistorial } from '../hooks/useLiquidaciones'

export function HistorialPage() {
  const [cohorteId, setCohorteId] = useState('')
  const [periodo, setPeriodo] = useState('')
  const [filtros, setFiltros] = useState<{ cohorteId?: string; periodo?: string }>({})

  const { data: historial = [], isLoading } = useHistorial(
    filtros.cohorteId,
    filtros.periodo,
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
        <div>
          <label className="block text-xs font-medium text-gray-600">Cohorte ID</label>
          <input
            type="text"
            value={cohorteId}
            onChange={(e) => setCohorteId(e.target.value)}
            placeholder="UUID (opcional)"
            className="mt-1 w-64 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Período</label>
          <input
            type="text"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
            placeholder="YYYY-MM (opcional)"
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={() => setFiltros({ cohorteId: cohorteId || undefined, periodo: periodo || undefined })}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Filtrar
        </button>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-400">Cargando historial…</p>
      ) : historial.length === 0 ? (
        <p className="text-sm text-gray-400">No hay liquidaciones cerradas con esos filtros.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-left">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Docente</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Rol</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Período</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-right text-gray-500">Total</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Estado</th>
              </tr>
            </thead>
            <tbody>
              {historial.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-gray-100 last:border-0 hover:bg-gray-50"
                >
                  <td className="py-3 px-4 text-sm text-gray-900">{row.nombre_docente}</td>
                  <td className="py-3 px-4 text-sm text-gray-600">{row.rol}</td>
                  <td className="py-3 px-4 text-sm text-gray-600">{row.periodo}</td>
                  <td className="py-3 px-4 text-sm text-right text-gray-900">
                    ${row.monto_total.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4 text-sm">
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                      {row.estado}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
