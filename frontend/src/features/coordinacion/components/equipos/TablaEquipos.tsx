// features/coordinacion/components/equipos/TablaEquipos.tsx
import { useState } from 'react'
import { useEquipos, useDeleteEquipo } from '../../hooks/useEquipos'
import type { EquipoDocente } from '../../types'

const PAGE_SIZE = 20

interface Props {
  onEdit: (equipo: EquipoDocente) => void
}

export function TablaEquipos({ onEdit }: Props) {
  const { data: equipos = [], isLoading } = useEquipos()
  const deleteEquipo = useDeleteEquipo()
  const [page, setPage] = useState(0)

  if (isLoading) {
    return <p className="text-gray-500">Cargando asignaciones...</p>
  }

  if (equipos.length === 0) {
    return (
      <p className="text-center text-gray-400 py-8">No hay asignaciones docentes registradas.</p>
    )
  }

  const totalPages = Math.ceil(equipos.length / PAGE_SIZE)
  const paginados = equipos.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div>
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Rol</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Usuario ID</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Materia ID</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Desde</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Hasta</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {paginados.map((asig) => (
            <tr key={asig.id} className="hover:bg-gray-50">
              <td className="px-4 py-2">
                <span className="inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                  {asig.rol}
                </span>
              </td>
              <td className="px-4 py-2 font-mono text-xs text-gray-500">{asig.usuario_id}</td>
              <td className="px-4 py-2 font-mono text-xs text-gray-500">{asig.materia_id ?? '—'}</td>
              <td className="px-4 py-2 text-gray-600">{asig.desde}</td>
              <td className="px-4 py-2 text-gray-600">{asig.hasta ?? '—'}</td>
              <td className="px-4 py-2 flex gap-2">
                <button
                  onClick={() => onEdit(asig)}
                  className="text-blue-600 hover:underline text-xs"
                >
                  Editar
                </button>
                <button
                  onClick={() => deleteEquipo.mutate(asig.id)}
                  disabled={deleteEquipo.isPending}
                  className="text-red-500 hover:underline text-xs disabled:opacity-50"
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1 rounded border disabled:opacity-40"
          >
            Anterior
          </button>
          <span className="text-gray-500">Página {page + 1} de {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1 rounded border disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  )
}
