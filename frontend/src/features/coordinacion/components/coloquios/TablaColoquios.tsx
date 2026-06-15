// features/coordinacion/components/coloquios/TablaColoquios.tsx
import { Fragment, useState } from 'react'
import { useColoquios, useDeleteColoquio, usePatchColoquio } from '../../hooks/useColoquios'
import type { ColoquioConvocatoria, ColoquioEstado } from '../../types'

const ESTADOS: ColoquioEstado[] = ['Abierta', 'Cerrada', 'Cancelada']
const ESTADO_CLASS: Record<ColoquioEstado, string> = {
  Abierta: 'bg-green-100 text-green-800',
  Cerrada: 'bg-gray-100 text-gray-700',
  Cancelada: 'bg-red-100 text-red-700',
}

export function TablaColoquios() {
  const { data: coloquios = [], isLoading } = useColoquios()
  const patch = usePatchColoquio()
  const remove = useDeleteColoquio()

  const [editingId, setEditingId] = useState<string | null>(null)
  const [instancia, setInstancia] = useState('')
  const [dias, setDias] = useState(7)
  const [cupos, setCupos] = useState(10)

  if (isLoading) return <p className="text-gray-500">Cargando coloquios...</p>

  if (coloquios.length === 0) {
    return <p className="text-center text-gray-400 py-8">No hay convocatorias de coloquio.</p>
  }

  const handleEstado = (id: string, estado: ColoquioEstado) => {
    patch.mutate({ id, payload: { estado } })
  }

  const handleDelete = (id: string) => {
    if (window.confirm('¿Eliminar esta convocatoria?')) {
      remove.mutate(id)
    }
  }

  const handleStartEdit = (c: ColoquioConvocatoria) => {
    setEditingId(c.id)
    setInstancia(c.instancia)
    setDias(c.dias_disponibles)
    setCupos(c.cupos_disponibles)
  }

  const handleSaveEdit = (id: string) => {
    patch.mutate(
      { id, payload: { instancia, dias_disponibles: dias, cupos_disponibles: cupos } },
      { onSuccess: () => setEditingId(null) },
    )
  }

  return (
    <table className="min-w-full divide-y divide-gray-200 text-sm">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Instancia</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Tipo</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Cupos</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Días inscripción</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Acciones</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {coloquios.map((c) => (
          <Fragment key={c.id}>
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-2 font-medium text-gray-900">{c.instancia}</td>
              <td className="px-4 py-2 text-gray-600">{c.tipo}</td>
              <td className="px-4 py-2 text-gray-600">{c.cupos_disponibles}</td>
              <td className="px-4 py-2 text-gray-600">{c.dias_disponibles}</td>
              <td className="px-4 py-2">
                <select
                  value={c.estado}
                  onChange={(e) => handleEstado(c.id, e.target.value as ColoquioEstado)}
                  disabled={patch.isPending}
                  className={`text-xs font-medium px-2 py-0.5 rounded border-0 cursor-pointer ${ESTADO_CLASS[c.estado]}`}
                >
                  {ESTADOS.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </td>
              <td className="px-4 py-2 flex gap-2">
                {editingId === c.id ? (
                  <>
                    <button
                      onClick={() => handleSaveEdit(c.id)}
                      disabled={patch.isPending}
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
                      onClick={() => handleStartEdit(c)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(c.id)}
                      disabled={remove.isPending}
                      className="text-xs text-red-500 hover:text-red-700 disabled:opacity-40"
                    >
                      Eliminar
                    </button>
                  </>
                )}
              </td>
            </tr>
            {editingId === c.id && (
              <tr className="bg-blue-50">
                <td colSpan={6} className="px-4 py-3">
                  <div className="flex gap-4 items-end">
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-600 mb-1">Instancia</label>
                      <input
                        value={instancia}
                        onChange={(e) => setInstancia(e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      />
                    </div>
                    <div className="w-28">
                      <label className="block text-xs font-medium text-gray-600 mb-1">Días</label>
                      <input
                        type="number"
                        min="1"
                        value={dias}
                        onChange={(e) => setDias(Number(e.target.value))}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      />
                    </div>
                    <div className="w-28">
                      <label className="block text-xs font-medium text-gray-600 mb-1">Cupos</label>
                      <input
                        type="number"
                        min="1"
                        value={cupos}
                        onChange={(e) => setCupos(Number(e.target.value))}
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
