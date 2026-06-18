// features/coordinacion/components/encuentros/TablaEncuentros.tsx
// Aligned with backend InstanciaEncuentro schema
import { useEncuentros } from '../../hooks/useEncuentros'
import type { InstanciaEncuentro, EstadoEncuentro } from '../../types'

const ESTADO_CLASS: Record<EstadoEncuentro, string> = {
  Programado: 'bg-blue-50 text-blue-700',
  Realizado: 'bg-green-50 text-green-700',
  Cancelado: 'bg-red-50 text-red-700',
}

function formatFecha(iso: string) {
  return new Date(iso).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

interface Props {
  onEdit?: (instancia: InstanciaEncuentro) => void
}

export function TablaEncuentros({ onEdit }: Props) {
  const { data: instancias = [], isLoading } = useEncuentros()

  if (isLoading) return <p className="text-gray-500">Cargando encuentros...</p>

  if (instancias.length === 0) {
    return <p className="text-center text-gray-400 py-8">No hay encuentros programados.</p>
  }

  return (
    <table className="min-w-full divide-y divide-gray-200 text-sm">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Fecha</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Hora</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Título</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Enlace</th>
          <th className="px-4 py-2 text-left font-medium text-gray-600">Grabación</th>
          {onEdit && <th className="px-4 py-2 text-left font-medium text-gray-600">Acciones</th>}
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {instancias.map((e) => (
          <tr key={e.id} className="hover:bg-gray-50">
            <td className="px-4 py-2 text-gray-900">{formatFecha(e.fecha)}</td>
            <td className="px-4 py-2 text-gray-600 font-mono text-xs">{e.hora}</td>
            <td className="px-4 py-2 font-medium text-gray-900">{e.titulo}</td>
            <td className="px-4 py-2">
              <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${ESTADO_CLASS[e.estado]}`}>{e.estado}</span>
            </td>
            <td className="px-4 py-2 text-xs">
              {e.meet_url ? <a href={e.meet_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Abrir</a> : '—'}
            </td>
            <td className="px-4 py-2 text-xs">
              {e.video_url ? <a href={e.video_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Ver</a> : '—'}
            </td>
            {onEdit && (
              <td className="px-4 py-2">
                <button onClick={() => onEdit(e)} className="text-blue-600 hover:underline text-xs">Editar</button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
