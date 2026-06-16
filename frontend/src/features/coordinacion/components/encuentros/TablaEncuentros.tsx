// features/coordinacion/components/encuentros/TablaEncuentros.tsx
import { Fragment, useState } from 'react'
import { useEncuentros, useUpdateInstancia } from '../../hooks/useEncuentros'
import type { EncuentroAdmin } from '../../types'

const ESTADOS = ['Programado', 'Realizado', 'Cancelado'] as const
const ESTADO_CLASS: Record<string, string> = {
  Programado: 'bg-blue-100 text-blue-700',
  Realizado: 'bg-green-100 text-green-800',
  Cancelado: 'bg-gray-100 text-gray-500',
}

export function TablaEncuentros() {
  const { data: encuentros = [], isLoading } = useEncuentros()
  const update = useUpdateInstancia()

  const [editingId, setEditingId] = useState<string | null>(null)
  const [meetUrl, setMeetUrl] = useState('')
  const [comentario, setComentario] = useState('')

  if (isLoading) return <p className="text-gray-500">Cargando encuentros...</p>

  if (encuentros.length === 0) {
    return <p className="text-center text-gray-400 py-8">No hay encuentros programados.</p>
  }

  const handleEstado = (id: string, estado: string) => {
    update.mutate({ id, payload: { estado } })
  }

  const handleStartEdit = (e: EncuentroAdmin) => {
    setEditingId(e.id)
    setMeetUrl(e.meet_url ?? '')
    setComentario(e.comentario ?? '')
  }

  const handleSaveEdit = (id: string) => {
    update.mutate(
      { id, payload: { meet_url: meetUrl || null, comentario: comentario || null } },
      { onSuccess: () => setEditingId(null) },
    )
  }

  const handleCancelar = (id: string) => {
    if (window.confirm('¿Cancelar este encuentro? El estado cambiará a "Cancelado".')) {
      update.mutate({ id, payload: { estado: 'Cancelado' } })
    }
  }

  return (
    <table className="min-w-full divide-y divide-gray-200 text-sm">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Fecha</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Hora</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Título</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Meet</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Acciones</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {encuentros.map((e) => (
          <Fragment key={e.id}>
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-2 text-gray-900">
                {new Date(e.fecha.slice(0, 10) + 'T12:00:00').toLocaleDateString('es-AR')}
              </td>
              <td className="px-4 py-2 text-gray-600">{e.hora}</td>
              <td className="px-4 py-2 text-gray-900">{e.titulo}</td>
              <td className="px-4 py-2">
                <select
                  value={e.estado}
                  onChange={(ev) => handleEstado(e.id, ev.target.value)}
                  disabled={update.isPending}
                  className={`text-xs font-medium px-2 py-0.5 rounded border-0 cursor-pointer ${ESTADO_CLASS[e.estado] ?? 'bg-gray-100 text-gray-600'}`}
                >
                  {ESTADOS.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </td>
              <td className="px-4 py-2">
                {e.meet_url
                  ? <a href={e.meet_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs">Unirse</a>
                  : <span className="text-gray-400">—</span>
                }
              </td>
              <td className="px-4 py-2 flex gap-2">
                {editingId === e.id ? (
                  <>
                    <button
                      onClick={() => handleSaveEdit(e.id)}
                      disabled={update.isPending}
                      className="text-xs text-green-600 hover:text-green-800 disabled:opacity-40"
                    >
                      Guardar
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      Cancelar
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => handleStartEdit(e)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Editar
                    </button>
                    {e.estado !== 'Cancelado' && (
                      <button
                        onClick={() => handleCancelar(e.id)}
                        disabled={update.isPending}
                        className="text-xs text-red-500 hover:text-red-700 disabled:opacity-40"
                      >
                        Cancelar
                      </button>
                    )}
                  </>
                )}
              </td>
            </tr>
            {editingId === e.id && (
              <tr className="bg-blue-50">
                <td colSpan={6} className="px-4 py-3">
                  <div className="flex gap-4 items-end">
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-600 mb-1">Link Meet</label>
                      <input
                        type="url"
                        value={meetUrl}
                        onChange={(ev) => setMeetUrl(ev.target.value)}
                        placeholder="https://meet.google.com/..."
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      />
                    </div>
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-600 mb-1">Comentario</label>
                      <input
                        value={comentario}
                        onChange={(ev) => setComentario(ev.target.value)}
                        placeholder="Notas sobre el encuentro..."
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      />
                    </div>
                  </div>
                </td>
              </tr>
            )}
          </Fragment>
        ))}
      </tbody>
    </table>
  )
}
