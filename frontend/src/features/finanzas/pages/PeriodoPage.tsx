// features/finanzas/pages/PeriodoPage.tsx
import { useState } from 'react'
import { VistaPeriodo } from '../components/VistaPeriodo'
import { useCohortes } from '@/features/admin/hooks/useEstructura'

export function PeriodoPage() {
  const [cohorteId, setCohorteId] = useState('')
  const [periodo, setPeriodo] = useState('')
  const { data: cohortes = [] } = useCohortes()
  const [filtrosAplicados, setFiltrosAplicados] = useState<{
    cohorteId: string
    periodo: string
  } | null>(null)

  function handleBuscar() {
    if (cohorteId && periodo) {
      setFiltrosAplicados({ cohorteId, periodo })
    }
  }

  return (
    <div className="space-y-6">
      {/* Filtros */}
      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
        <div>
          <label className="block text-xs font-medium text-gray-600">Cohorte</label>
          <select
            value={cohorteId}
            onChange={(e) => setCohorteId(e.target.value)}
            className="mt-1 w-72 rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Seleccionar…</option>
            {cohortes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.plan ? `${c.plan} (${c.anio})` : `Cohorte ${c.anio}`}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Período</label>
          <input
            type="text"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
            placeholder="ej: 2026-1"
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={handleBuscar}
          disabled={!cohorteId || !periodo}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          Ver liquidaciones
        </button>
      </div>

      {filtrosAplicados ? (
        <VistaPeriodo cohorteId={filtrosAplicados.cohorteId} periodo={filtrosAplicados.periodo} />
      ) : (
        <p className="text-sm text-gray-400">
          Seleccioná una cohorte y un período para ver las liquidaciones.
        </p>
      )}
    </div>
  )
}
