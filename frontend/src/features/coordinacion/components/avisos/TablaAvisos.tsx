// features/coordinacion/components/avisos/TablaAvisos.tsx
import { useAvisos, useArchivarAviso } from '../../hooks/useAvisos'
import { TableSkeleton } from '@/shared/components/TableSkeleton'
import type { Aviso } from '../../types'

function formatDt(iso: string) {
  return new Date(iso).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

interface Props {
  onEdit: (aviso: Aviso) => void
}

export function TablaAvisos({ onEdit }: Props) {
  const { data: avisos = [], isLoading } = useAvisos()
  const archivarAviso = useArchivarAviso()

  if (isLoading) {
    return <TableSkeleton rows={4} cols={5} />
  }

  if (avisos.length === 0) {
    return (
      <p className="text-center text-gray-400 py-8">No hay avisos publicados.</p>
    )
  }

  return (
    <table className="min-w-full divide-y divide-gray-200 text-sm">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Título</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Audiencia</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Vigencia</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Acciones</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {avisos.map((aviso) => (
          <tr key={aviso.id} className={!aviso.activo ? 'opacity-50' : 'hover:bg-gray-50'}>
            <td className="px-4 py-2 font-medium text-gray-900">{aviso.titulo}</td>
            <td className="px-4 py-2 text-gray-600">
              {aviso.scope === 'TODOS' ? 'Todos' : `${aviso.scope}${aviso.scope_valor ? `: ${aviso.scope_valor}` : ''}`}
            </td>
            <td className="px-4 py-2 text-gray-600 whitespace-nowrap">
              {formatDt(aviso.vig_desde)} – {formatDt(aviso.vig_hasta)}
            </td>
            <td className="px-4 py-2 text-gray-600">
              {aviso.activo ? 'Activo' : 'Archivado'}
            </td>
            <td className="px-4 py-2 flex gap-3">
              {aviso.activo && (
                <>
                  <button
                    onClick={() => onEdit(aviso)}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => {
                      if (window.confirm('¿Archivar este aviso? Dejará de ser visible para los destinatarios.')) {
                        archivarAviso.mutate(aviso.id)
                      }
                    }}
                    disabled={archivarAviso.isPending}
                    className="text-xs text-orange-600 hover:underline disabled:opacity-50"
                  >
                    Archivar
                  </button>
                </>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
