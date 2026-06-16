// features/finanzas/components/VistaPeriodo.tsx
// Vista de liquidaciones del período: segmentada en general/NEXO/facturantes + KPIs
import { useState } from 'react'
import { useCerrarPeriodo, useVistaPeriodo } from '../hooks/useLiquidaciones'
import type { LiquidacionRow } from '../types'

interface Props {
  cohorteId: string
  periodo: string
}

function KPICard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">
        ${value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
      </p>
    </div>
  )
}

function FilaLiquidacion({ row }: { row: LiquidacionRow }) {
  return (
    <tr className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
      <td className="py-3 px-4 text-sm text-gray-900">{row.nombre_docente}</td>
      <td className="py-3 px-4 text-sm text-gray-600">{row.rol}</td>
      <td className="py-3 px-4 text-sm text-right text-gray-900">
        ${row.monto_base.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
      </td>
      <td className="py-3 px-4 text-sm text-right text-gray-900">
        ${row.monto_plus.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
      </td>
      <td className="py-3 px-4 text-sm text-right font-medium text-gray-900">
        ${row.monto_total.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
      </td>
      <td className="py-3 px-4 text-sm">
        <span
          className={[
            'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
            row.estado === 'cerrada'
              ? 'bg-green-100 text-green-700'
              : 'bg-yellow-100 text-yellow-700',
          ].join(' ')}
        >
          {row.estado}
        </span>
      </td>
    </tr>
  )
}

function TablaSegmento({ rows, titulo }: { rows: LiquidacionRow[]; titulo: string }) {
  if (rows.length === 0) {
    return (
      <div className="mb-6">
        <h3 className="mb-2 text-sm font-semibold text-gray-700">{titulo}</h3>
        <p className="text-sm text-gray-400">Sin registros en este segmento.</p>
      </div>
    )
  }
  return (
    <div className="mb-6">
      <h3 className="mb-2 text-sm font-semibold text-gray-700">{titulo}</h3>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-left">
          <thead className="bg-gray-50">
            <tr>
              <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Docente</th>
              <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Rol</th>
              <th className="py-3 px-4 text-xs font-semibold uppercase text-right text-gray-500">Base</th>
              <th className="py-3 px-4 text-xs font-semibold uppercase text-right text-gray-500">Plus</th>
              <th className="py-3 px-4 text-xs font-semibold uppercase text-right text-gray-500">Total</th>
              <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Estado</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <FilaLiquidacion key={row.id} row={row} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function VistaPeriodo({ cohorteId, periodo }: Props) {
  const { data, isLoading, isError } = useVistaPeriodo(cohorteId, periodo)
  const cerrar = useCerrarPeriodo()
  const [confirmOpen, setConfirmOpen] = useState(false)

  if (isLoading) {
    return <div className="py-8 text-center text-sm text-gray-400">Cargando liquidaciones…</div>
  }

  if (isError || !data) {
    return (
      <div className="py-8 text-center text-sm text-red-500">
        Error al cargar el período. Verificá los filtros.
      </div>
    )
  }

  const puedesCerrar =
    data.general.some((r) => r.estado === 'abierta') ||
    data.nexo.some((r) => r.estado === 'abierta') ||
    data.facturantes.some((r) => r.estado === 'abierta')

  function handleCerrar() {
    cerrar.mutate(
      { cohorte_id: cohorteId, periodo },
      { onSuccess: () => setConfirmOpen(false) },
    )
  }

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KPICard label="Total sin factura" value={data.kpis.total_sin_factura} />
        <KPICard label="Total con factura" value={data.kpis.total_con_factura} />
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Docentes</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{data.kpis.cantidad_docentes}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-400">NEXOs</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{data.kpis.cantidad_nexos}</p>
        </div>
      </div>

      {/* Botón cerrar */}
      {puedesCerrar && (
        <div className="flex justify-end">
          <button
            onClick={() => setConfirmOpen(true)}
            className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            disabled={cerrar.isPending}
          >
            Cerrar período
          </button>
        </div>
      )}

      {/* Modal de confirmación */}
      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-bold text-gray-900">Confirmar cierre</h2>
            <p className="mt-2 text-sm text-gray-600">
              Al cerrar el período <strong>{periodo}</strong> las liquidaciones quedarán
              <strong> inmutables</strong>. Esta acción no se puede deshacer.
            </p>
            <div className="mt-4 flex justify-end gap-3">
              <button
                onClick={() => setConfirmOpen(false)}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleCerrar}
                disabled={cerrar.isPending}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {cerrar.isPending ? 'Cerrando…' : 'Confirmar cierre'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Segmentos */}
      <TablaSegmento rows={data.general} titulo="General" />
      <TablaSegmento rows={data.nexo} titulo="NEXO" />
      <TablaSegmento rows={data.facturantes} titulo="Facturantes" />
    </div>
  )
}
