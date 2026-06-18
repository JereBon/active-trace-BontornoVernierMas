import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useLoteStatus, useAprobarLote, useCancelarLote, useLotesByMateria } from '../hooks/useAprobaciones'
import { getMaterias } from '@/features/admin/services/estructuraService'

const ESTADO_COLORS: Record<string, string> = {
  Pendiente: 'bg-yellow-50 text-yellow-700',
  Enviando: 'bg-blue-50 text-blue-700',
  Enviado: 'bg-green-50 text-green-700',
  Error: 'bg-red-50 text-red-700',
  Cancelado: 'bg-gray-100 text-gray-500',
}

export function AprobacionesPage() {
  const [inputId, setInputId] = useState('')
  const [loteId, setLoteId] = useState<string | null>(null)
  const [materiaId, setMateriaId] = useState('')

  const { data: materias = [] } = useQuery({ queryKey: ['materias'], queryFn: getMaterias })
  const { data: lotesResumen = [], isLoading: loadingLotes } = useLotesByMateria(materiaId || null)
  const { data: lote, isLoading, error } = useLoteStatus(loteId)
  const aprobar = useAprobarLote(loteId)
  const cancelar = useCancelarLote(loteId)

  const isValidUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(inputId)

  function buscar() {
    if (isValidUUID) setLoteId(inputId.trim())
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-800">Aprobación de Comunicaciones</h2>
        <p className="text-sm text-gray-500 mt-1">
          Seleccioná una materia para ver los lotes pendientes, o buscá un lote específico por ID.
        </p>
      </div>

      {/* Selector de materia + buscador */}
      <div className="flex gap-3 items-end">
        <div>
          <label htmlFor="mat-aprob" className="block text-sm font-medium text-gray-700 mb-1">Materia</label>
          <select
            id="mat-aprob"
            value={materiaId}
            onChange={(e) => { setMateriaId(e.target.value); setLoteId(null) }}
            className="border border-gray-300 rounded px-3 py-2 text-sm w-56"
          >
            <option value="">Seleccioná una materia</option>
            {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
          </select>
        </div>
        <div className="flex-1">
          <label htmlFor="lote-id" className="block text-sm font-medium text-gray-700 mb-1">O buscá por ID de lote</label>
          <input
            id="lote-id"
            value={inputId}
            onChange={(e) => setInputId(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && buscar()}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono"
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
          />
        </div>
        <button onClick={buscar} disabled={!isValidUUID} className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-40">
          Buscar
        </button>
      </div>

      {/* Lista de lotes por materia */}
      {materiaId && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Lotes pendientes</h3>
          {loadingLotes ? (
            <p className="text-sm text-gray-400">Cargando lotes…</p>
          ) : lotesResumen.length === 0 ? (
            <p className="text-sm text-gray-400">No hay lotes para esta materia.</p>
          ) : (
            <div className="space-y-2">
              {lotesResumen.map((l) => (
                <div
                  key={l.lote_id}
                  className={`flex items-center justify-between p-3 rounded border cursor-pointer hover:bg-gray-50 ${loteId === l.lote_id ? 'border-blue-400 bg-blue-50' : 'border-gray-200'}`}
                  onClick={() => { setLoteId(l.lote_id); setInputId('') }}
                >
                  <div className="flex gap-4 text-sm">
                    <span className="font-mono text-xs text-gray-400">{l.lote_id.slice(0, 8)}…</span>
                    <span>Total: <strong>{l.total}</strong></span>
                    <span>Pendientes: <strong className="text-yellow-600">{l.pendientes}</strong></span>
                    <span>Enviados: <strong className="text-green-600">{l.enviados}</strong></span>
                    {!l.aprobado && l.pendientes > 0 && <span className="text-orange-600 text-xs font-medium">Requiere aprobación</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Detalle del lote seleccionado */}
      {isLoading && <p className="text-sm text-gray-400">Cargando lote…</p>}
      {error && <p className="text-sm text-red-600">No se encontró el lote o no tenés acceso a él.</p>}

      {lote && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 font-mono">{lote.lote_id}</p>
              <div className="flex gap-4 mt-2 text-sm text-gray-700">
                <span>Total: <strong>{lote.total}</strong></span>
                <span>Pendientes: <strong className="text-yellow-600">{lote.pendientes}</strong></span>
                <span>Enviados: <strong className="text-green-600">{lote.enviados}</strong></span>
                <span>Errores: <strong className="text-red-600">{lote.errores}</strong></span>
                <span>Cancelados: <strong className="text-gray-500">{lote.cancelados}</strong></span>
              </div>
            </div>

            {lote.pendientes > 0 && (
              <div className="flex gap-2">
                <button onClick={() => aprobar.mutate()} disabled={aprobar.isPending} className="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50">
                  {aprobar.isPending ? 'Aprobando…' : `Aprobar ${lote.pendientes} mensajes`}
                </button>
                <button onClick={() => cancelar.mutate()} disabled={cancelar.isPending} className="px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50">
                  {cancelar.isPending ? 'Cancelando…' : 'Cancelar lote'}
                </button>
              </div>
            )}
          </div>

          {aprobar.isSuccess && (
            <p className="text-sm text-green-700 bg-green-50 rounded px-3 py-2">
              Lote aprobado. {(aprobar.data as { approved: number })?.approved ?? 0} mensajes serán enviados por el worker.
            </p>
          )}
          {cancelar.isSuccess && (
            <p className="text-sm text-gray-600 bg-gray-50 rounded px-3 py-2">Lote cancelado.</p>
          )}

          {lote.mensajes.length > 0 && (
            <table className="min-w-full divide-y divide-gray-200 text-sm mt-2">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Destinatario</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Asunto</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {lote.mensajes.map((m) => (
                  <tr key={m.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-gray-700">{m.destinatario}</td>
                    <td className="px-4 py-2 text-gray-600 text-xs">{m.asunto}</td>
                    <td className="px-4 py-2">
                      <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${ESTADO_COLORS[m.estado] ?? 'bg-gray-100 text-gray-600'}`}>{m.estado}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
