// features/coordinacion/components/avisos/TablaAvisos.tsx
import { useAvisos, useArchivarAviso } from '../../hooks/useAvisos'
import type { AvisoSeveridad } from '../../types'

const SEVERIDAD_CLASS: Record<AvisoSeveridad, string> = {
  info: 'bg-blue-100 text-blue-800',
  advertencia: 'bg-yellow-100 text-yellow-800',
  critico: 'bg-red-100 text-red-800',
}

export function TablaAvisos() {
  const { data: avisos = [], isLoading } = useAvisos()
  const archivarAviso = useArchivarAviso()

  if (isLoading) {
    return <p className="text-gray-500">Cargando avisos...</p>
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
          <th className="px-4 py-2 text-left font-medium text-gray-600">Severidad</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Scope</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Ack</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Acciones</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {avisos.map((aviso) => (
          <tr key={aviso.id} className={aviso.archivado ? 'opacity-50' : 'hover:bg-gray-50'}>
            <td className="px-4 py-2 font-medium text-gray-900">{aviso.titulo}</td>
            <td className="px-4 py-2">
              <span
                className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${SEVERIDAD_CLASS[aviso.severidad]}`}
              >
                {aviso.severidad}
              </span>
            </td>
            <td className="px-4 py-2 text-gray-600">{aviso.scope}</td>
            <td className="px-4 py-2 text-gray-600">{aviso.requiere_ack ? 'Sí' : 'No'}</td>
            <td className="px-4 py-2 text-gray-600">
              {aviso.archivado ? 'Archivado' : 'Activo'}
            </td>
            <td className="px-4 py-2">
              {!aviso.archivado && (
                <button
                  onClick={() => archivarAviso.mutate(aviso.id)}
                  disabled={archivarAviso.isPending}
                  className="text-xs text-orange-600 hover:underline disabled:opacity-50"
                >
                  Archivar
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
