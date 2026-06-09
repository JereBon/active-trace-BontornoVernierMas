// features/admin/components/PanelAuditoria.tsx
// Panel de auditoría: métricas + tabla de log con filtros
import { useState } from 'react'
import { useAuditoriaLog, usePanelMetricas } from '../hooks/useAuditoria'
import type { LogFiltros } from '../types'

function MetricaCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value.toLocaleString()}</p>
    </div>
  )
}

export function PanelAuditoria() {
  const { data: panel, isLoading: loadingPanel } = usePanelMetricas()
  const [filtros, setFiltros] = useState<LogFiltros>({ limit: 50, offset: 0 })
  const [inputFiltros, setInputFiltros] = useState({ accion: '', fecha_desde: '', fecha_hasta: '' })
  const { data: log, isLoading: loadingLog } = useAuditoriaLog(filtros)

  function aplicarFiltros() {
    setFiltros({
      accion: inputFiltros.accion || undefined,
      fecha_desde: inputFiltros.fecha_desde || undefined,
      fecha_hasta: inputFiltros.fecha_hasta || undefined,
      limit: 50,
      offset: 0,
    })
  }

  return (
    <div className="space-y-6">
      {/* Panel de métricas */}
      {loadingPanel ? (
        <p className="text-sm text-gray-400">Cargando métricas…</p>
      ) : panel ? (
        <section aria-label="panel-metricas">
          <h2 className="mb-3 text-base font-semibold text-gray-900">Métricas generales</h2>
          {(panel.total_acciones != null || panel.acciones_hoy != null) && (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
              {panel.total_acciones != null && (
                <MetricaCard label="Total acciones" value={panel.total_acciones} />
              )}
              {panel.acciones_hoy != null && (
                <MetricaCard label="Acciones hoy" value={panel.acciones_hoy} />
              )}
            </div>
          )}

          {panel.top_acciones && panel.top_acciones.length > 0 && (
            <div className="mt-4">
              <h3 className="mb-2 text-sm font-medium text-gray-700">Top acciones</h3>
              <ul className="space-y-1">
                {panel.top_acciones.map((a) => (
                  <li key={a.accion} className="flex justify-between text-sm text-gray-700">
                    <span className="font-mono text-xs">{a.accion}</span>
                    <span>{a.cantidad}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {panel.por_materia && panel.por_materia.length > 0 && (
            <div className="mt-4">
              <h3 className="mb-2 text-sm font-medium text-gray-700">Por materia</h3>
              <ul className="space-y-1">
                {panel.por_materia.map((m, i) => (
                  <li key={i} className="flex justify-between text-sm text-gray-700">
                    <span>{m.nombre ?? '—'}</span>
                    <span>{m.cantidad}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      ) : null}

      {/* Filtros del log */}
      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-900">Log de auditoría</h2>
        <div className="mb-4 flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3">
          <div>
            <label className="block text-xs font-medium text-gray-600">Acción</label>
            <input
              type="text"
              value={inputFiltros.accion}
              onChange={(e) => setInputFiltros((f) => ({ ...f, accion: e.target.value }))}
              placeholder="crear_usuario"
              className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600">Desde</label>
            <input
              type="date"
              value={inputFiltros.fecha_desde}
              onChange={(e) => setInputFiltros((f) => ({ ...f, fecha_desde: e.target.value }))}
              className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600">Hasta</label>
            <input
              type="date"
              value={inputFiltros.fecha_hasta}
              onChange={(e) => setInputFiltros((f) => ({ ...f, fecha_hasta: e.target.value }))}
              className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={aplicarFiltros}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Filtrar
          </button>
        </div>

        {/* Tabla log */}
        {loadingLog ? (
          <p className="text-sm text-gray-400">Cargando log…</p>
        ) : !log || log.items.length === 0 ? (
          <p className="text-sm text-gray-400">No hay entradas en el log con esos filtros.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-left" aria-label="tabla-log">
              <thead className="bg-gray-50">
                <tr>
                  <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Fecha</th>
                  <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Actor</th>
                  <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Acción</th>
                  <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Recurso</th>
                  <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">IP</th>
                </tr>
              </thead>
              <tbody>
                {log.items.map((entry) => (
                  <tr key={entry.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                    <td className="py-2 px-4 text-xs text-gray-500">
                      {new Date(entry.created_at).toLocaleString('es-AR')}
                    </td>
                    <td className="py-2 px-4 text-sm text-gray-700">
                      {entry.actor_nombre ?? entry.actor_id}
                    </td>
                    <td className="py-2 px-4 font-mono text-xs text-gray-900">{entry.accion}</td>
                    <td className="py-2 px-4 text-xs text-gray-600">
                      {entry.recurso_tipo ?? '—'}
                    </td>
                    <td className="py-2 px-4 text-xs text-gray-500">{entry.ip ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="flex items-center justify-between border-t border-gray-100 px-4 py-2">
              <p className="text-xs text-gray-500">
                {log.items.length} de {log.total} entradas
              </p>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
