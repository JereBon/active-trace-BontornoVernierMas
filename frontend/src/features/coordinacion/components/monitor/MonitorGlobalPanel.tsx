// features/coordinacion/components/monitor/MonitorGlobalPanel.tsx
import { useState } from 'react'
import { useMonitorGlobal } from '../../hooks/useMonitorGlobal'

export function MonitorGlobalPanel() {
  const [comision, setComision] = useState('')
  const [regional, setRegional] = useState('')

  const params = {
    ...(comision ? { comision } : {}),
    ...(regional ? { regional } : {}),
  }

  const { data: items = [], isLoading } = useMonitorGlobal(params)

  if (isLoading) {
    return <p className="text-gray-500">Cargando monitor...</p>
  }

  return (
    <div>
      <div className="mb-4 flex gap-4">
        <input
          value={comision}
          onChange={(e) => setComision(e.target.value)}
          placeholder="Filtrar comisión"
          className="border border-gray-300 rounded px-3 py-2 text-sm w-40"
        />
        <input
          value={regional}
          onChange={(e) => setRegional(e.target.value)}
          placeholder="Filtrar regional"
          className="border border-gray-300 rounded px-3 py-2 text-sm w-40"
        />
      </div>

      {items.length === 0 ? (
        <p className="text-center text-gray-400 py-8">No hay datos de monitor disponibles.</p>
      ) : (
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Alumno</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Comisión</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Regional</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Aprobadas</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Atrasado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.map((item) => (
              <tr key={item.entrada_padron_id} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-gray-900">
                  {item.apellidos}, {item.nombre}
                </td>
                <td className="px-4 py-2 text-gray-600">{item.comision ?? '—'}</td>
                <td className="px-4 py-2 text-gray-600">{item.regional ?? '—'}</td>
                <td className="px-4 py-2 text-gray-600">
                  {item.cant_aprobadas}/{item.cant_actividades}
                </td>
                <td className="px-4 py-2">
                  {item.es_atrasado ? (
                    <span className="text-red-600 font-medium">Sí</span>
                  ) : (
                    <span className="text-green-600">No</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
