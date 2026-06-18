import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonitorGlobal } from '../../hooks/useMonitorGlobal'
import { exportMonitorToCsv } from '../../services/monitorService'
import { getMaterias } from '@/features/admin/services/estructuraService'

export function MonitorGlobalPanel() {
  const [comision, setComision] = useState('')
  const [regional, setRegional] = useState('')
  const [materiaId, setMateriaId] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [soloAtrasados, setSoloAtrasados] = useState(false)
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')

  const { data: materias = [] } = useQuery({ queryKey: ['materias'], queryFn: getMaterias })

  const params = {
    ...(comision ? { comision } : {}),
    ...(regional ? { regional } : {}),
    ...(materiaId ? { materia_id: materiaId } : {}),
    ...(busqueda ? { alumno_nombre: busqueda } : {}),
    ...(soloAtrasados ? { solo_atrasados: true } : {}),
    ...(fechaDesde ? { fecha_desde: fechaDesde } : {}),
    ...(fechaHasta ? { fecha_hasta: fechaHasta } : {}),
  }

  const { data: items = [], isLoading } = useMonitorGlobal(params)

  if (isLoading) {
    return <p className="text-gray-500">Cargando monitor...</p>
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar alumno…"
          className="border border-gray-300 rounded px-3 py-2 text-sm w-44"
        />
        <select
          value={materiaId}
          onChange={(e) => setMateriaId(e.target.value)}
          className="border border-gray-300 rounded px-2 py-2 text-sm"
          aria-label="Materia"
        >
          <option value="">Todas las materias</option>
          {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
        </select>
        <input
          value={comision}
          onChange={(e) => setComision(e.target.value)}
          placeholder="Comisión"
          className="border border-gray-300 rounded px-3 py-2 text-sm w-32"
        />
        <input
          value={regional}
          onChange={(e) => setRegional(e.target.value)}
          placeholder="Regional"
          className="border border-gray-300 rounded px-3 py-2 text-sm w-32"
        />
        <input
          type="date"
          value={fechaDesde}
          onChange={(e) => setFechaDesde(e.target.value)}
          className="border border-gray-300 rounded px-2 py-2 text-sm"
          aria-label="Fecha desde"
        />
        <input
          type="date"
          value={fechaHasta}
          onChange={(e) => setFechaHasta(e.target.value)}
          className="border border-gray-300 rounded px-2 py-2 text-sm"
          aria-label="Fecha hasta"
        />
        <label className="flex items-center gap-1 text-sm">
          <input type="checkbox" checked={soloAtrasados} onChange={(e) => setSoloAtrasados(e.target.checked)} />
          Solo atrasados
        </label>
        <button
          onClick={() => exportMonitorToCsv(items)}
          disabled={items.length === 0}
          className="ml-auto px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40"
        >
          Exportar CSV
        </button>
      </div>

      {items.length === 0 ? (
        <p className="text-center text-gray-400 py-8">No hay datos de monitor disponibles.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Alumno</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Comisión</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Regional</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Actividades</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Aprobadas</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">No Aprobadas</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Faltantes</th>
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
                  <td className="px-4 py-2 text-gray-600">{item.cant_actividades}</td>
                  <td className="px-4 py-2 text-gray-600">{item.cant_aprobadas}</td>
                  <td className="px-4 py-2 text-gray-600">{item.cant_no_aprobadas}</td>
                  <td className="px-4 py-2 text-gray-600">{item.cant_faltantes}</td>
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
          <p className="text-xs text-gray-400 mt-2">{items.length} registros</p>
        </div>
      )}
    </div>
  )
}
