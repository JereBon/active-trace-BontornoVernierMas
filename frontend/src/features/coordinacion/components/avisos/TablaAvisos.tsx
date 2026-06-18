// features/coordinacion/components/avisos/TablaAvisos.tsx
import { useAvisos, useDesactivarAviso } from '../../hooks/useAvisos'
import type { AvisoScope } from '../../types'

const SCOPE_LABEL: Record<AvisoScope, string> = {
  TODOS: 'Todos',
  ROL: 'Por rol',
  USUARIO: 'Usuario',
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('es-AR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function TablaAvisos() {
  const { data: avisos = [], isLoading } = useAvisos()
  const desactivar = useDesactivarAviso()

  if (isLoading) return <p className="text-gray-500">Cargando avisos...</p>

  if (avisos.length === 0) {
    return <p className="text-center text-gray-400 py-8">No hay avisos publicados.</p>
  }

  return (
    <table className="min-w-full divide-y divide-gray-200 text-sm">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Título</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Alcance</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Vigencia desde</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Vigencia hasta</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Acciones</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {avisos.map((aviso) => {
          const ahora = new Date()
          const desde = new Date(aviso.vig_desde)
          const hasta = new Date(aviso.vig_hasta)
          const enVigencia = aviso.activo && ahora >= desde && ahora <= hasta
          const vencido = ahora > hasta

          return (
            <tr key={aviso.id} className={!aviso.activo ? 'opacity-50' : 'hover:bg-gray-50'}>
              <td className="px-4 py-2 font-medium text-gray-900">{aviso.titulo}</td>
              <td className="px-4 py-2 text-gray-600">
                {SCOPE_LABEL[aviso.scope as AvisoScope]}
                {aviso.scope_valor && (
                  <span className="ml-1 text-xs text-gray-400">({aviso.scope_valor})</span>
                )}
              </td>
              <td className="px-4 py-2 text-gray-600 text-xs whitespace-nowrap">{formatDate(aviso.vig_desde)}</td>
              <td className="px-4 py-2 text-gray-600 text-xs whitespace-nowrap">{formatDate(aviso.vig_hasta)}</td>
              <td className="px-4 py-2">
                {!aviso.activo ? (
                  <span className="text-xs text-gray-400">Desactivado</span>
                ) : vencido ? (
                  <span className="text-xs text-orange-500">Vencido</span>
                ) : enVigencia ? (
                  <span className="text-xs font-medium text-green-600">Activo</span>
                ) : (
                  <span className="text-xs text-blue-500">Programado</span>
                )}
              </td>
              <td className="px-4 py-2">
                {aviso.activo && (
                  <button
                    onClick={() => desactivar.mutate(aviso.id)}
                    disabled={desactivar.isPending}
                    className="text-xs text-red-500 hover:underline disabled:opacity-50"
                  >
                    Desactivar
                  </button>
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
