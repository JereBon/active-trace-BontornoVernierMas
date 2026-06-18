import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useEquipos, useDeleteEquipo } from '../../hooks/useEquipos'
import { getUsuarios } from '../../services/equiposService'
import { getCarreras, getCohortes, getMaterias } from '@/features/admin/services/estructuraService'
import type { Asignacion, AsignacionFilter, RolAsignacion } from '../../types'
import { ROLES_ASIGNACION } from '../../types'
import { api } from '@/shared/services/api'

const PAGE_SIZE = 20

interface Props {
  onEdit: (asignacion: Asignacion) => void
}

function estadoVigencia(desde: string, hasta: string | null): { label: string; cls: string } {
  const hoy = new Date()
  const d = new Date(desde)
  const h = hasta ? new Date(hasta) : null
  if (h && hoy > h) return { label: 'Vencido', cls: 'text-red-500' }
  if (hoy < d) return { label: 'Programado', cls: 'text-blue-500' }
  return { label: 'Vigente', cls: 'text-green-600 font-medium' }
}

export function TablaEquipos({ onEdit }: Props) {
  const deleteEquipo = useDeleteEquipo()
  const [page, setPage] = useState(0)
  const [rolFilter, setRolFilter] = useState<RolAsignacion | ''>('')
  const [estadoFilter, setEstadoFilter] = useState<'vigente' | 'vencido' | ''>('')
  const [materiaFilter, setMateriaFilter] = useState('')
  const [carreraFilter, setCarreraFilter] = useState('')
  const [cohorteFilter, setCohorteFilter] = useState('')

  const serverFilters: AsignacionFilter = {
    rol: rolFilter || undefined,
    materia_id: materiaFilter || undefined,
    carrera_id: carreraFilter || undefined,
    cohorte_id: cohorteFilter || undefined,
  }

  const { data: asignaciones = [], isLoading } = useEquipos(serverFilters)
  const { data: usuarios = [] } = useQuery({ queryKey: ['usuarios'], queryFn: getUsuarios })
  const { data: materias = [] } = useQuery({ queryKey: ['materias'], queryFn: getMaterias })
  const { data: carreras = [] } = useQuery({ queryKey: ['carreras'], queryFn: getCarreras })
  const { data: cohortes = [] } = useQuery({ queryKey: ['cohortes-all'], queryFn: () => getCohortes() })

  const userMap = Object.fromEntries(usuarios.map((u) => [u.id, `${u.nombre}${u.apellidos ? ' ' + u.apellidos : ''}`]))
  const materiaMap = Object.fromEntries(materias.map((m) => [m.id, m.nombre]))
  const carreraMap = Object.fromEntries(carreras.map((c) => [c.id, c.nombre]))
  const cohorteMap = Object.fromEntries(cohortes.map((c) => [c.id, c.nombre]))

  if (isLoading) return <p className="text-gray-500">Cargando asignaciones...</p>

  const activas = asignaciones.filter((a) => a.deleted_at === null)

  const filtered = activas.filter((a) => {
    if (estadoFilter) {
      const est = estadoVigencia(a.desde, a.hasta)
      if (estadoFilter === 'vigente' && est.label !== 'Vigente') return false
      if (estadoFilter === 'vencido' && est.label !== 'Vencido') return false
    }
    return true
  })

  if (!isLoading && asignaciones.length === 0 && !rolFilter && !materiaFilter && !carreraFilter && !cohorteFilter && !estadoFilter) {
    return <p className="text-center text-gray-400 py-8">No hay asignaciones docentes registradas.</p>
  }

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  function handleExportar() {
    api.get('/v1/equipos/exportar', { responseType: 'blob' }).then(({ data }) => {
      const url = URL.createObjectURL(new Blob([data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'equipos.csv'
      a.click()
      URL.revokeObjectURL(url)
    })
  }

  return (
    <div className="space-y-3">
      {/* Filtros */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label htmlFor="rol-filter" className="text-sm text-gray-600">Rol</label>
          <select
            id="rol-filter"
            value={rolFilter}
            onChange={(e) => { setRolFilter(e.target.value as RolAsignacion | ''); setPage(0) }}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="">Todos</option>
            {ROLES_ASIGNACION.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="estado-filter" className="text-sm text-gray-600">Estado</label>
          <select
            id="estado-filter"
            value={estadoFilter}
            onChange={(e) => { setEstadoFilter(e.target.value as typeof estadoFilter); setPage(0) }}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="">Todos</option>
            <option value="vigente">Vigente</option>
            <option value="vencido">Vencido</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="materia-filter" className="text-sm text-gray-600">Materia</label>
          <select
            id="materia-filter"
            value={materiaFilter}
            onChange={(e) => { setMateriaFilter(e.target.value); setPage(0) }}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="">Todas</option>
            {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="carrera-filter" className="text-sm text-gray-600">Carrera</label>
          <select
            id="carrera-filter"
            value={carreraFilter}
            onChange={(e) => { setCarreraFilter(e.target.value); setPage(0) }}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="">Todas</option>
            {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="cohorte-filter" className="text-sm text-gray-600">Cohorte</label>
          <select
            id="cohorte-filter"
            value={cohorteFilter}
            onChange={(e) => { setCohorteFilter(e.target.value); setPage(0) }}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="">Todos</option>
            {cohortes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </div>
        <button
          onClick={handleExportar}
          className="ml-auto px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
        >
          Exportar CSV
        </button>
      </div>

      {filtered.length === 0 ? (
        <p className="text-center text-gray-400 py-6">Sin resultados para esos filtros.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Docente</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Rol</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Materia</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Carrera</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Cohorte</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Comisiones</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Vigencia</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {paginated.map((a) => {
                const est = estadoVigencia(a.desde, a.hasta)
                return (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-gray-900">
                      {userMap[a.usuario_id] ?? <span className="text-gray-400 font-mono text-xs">{a.usuario_id.slice(0, 8)}…</span>}
                    </td>
                    <td className="px-4 py-2">
                      <span className="inline-block rounded bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                        {a.rol}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-600">
                      {a.materia_id ? (materiaMap[a.materia_id] ?? <span className="text-gray-400 text-xs">{a.materia_id.slice(0, 8)}…</span>) : '—'}
                    </td>
                    <td className="px-4 py-2 text-gray-600">
                      {a.carrera_id ? (carreraMap[a.carrera_id] ?? '—') : '—'}
                    </td>
                    <td className="px-4 py-2 text-gray-600">
                      {a.cohorte_id ? (cohorteMap[a.cohorte_id] ?? '—') : '—'}
                    </td>
                    <td className="px-4 py-2">
                      {a.comisiones.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {a.comisiones.map((c, i) => (
                            <span key={i} className="inline-block rounded bg-purple-50 px-2 py-0.5 text-xs text-purple-700">
                              {c}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-gray-600 text-xs whitespace-nowrap">
                      {a.desde} → {a.hasta ?? '∞'}
                    </td>
                    <td className={`px-4 py-2 text-xs ${est.cls}`}>{est.label}</td>
                    <td className="px-4 py-2 flex gap-2">
                      <button onClick={() => onEdit(a)} className="text-blue-600 hover:underline text-xs">
                        Editar
                      </button>
                      <button
                        onClick={() => deleteEquipo.mutate(a.id)}
                        className="text-red-500 hover:underline text-xs"
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0} className="px-3 py-1 rounded border disabled:opacity-40">Anterior</button>
          <span className="text-gray-500">Página {page + 1} de {totalPages}</span>
          <button onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="px-3 py-1 rounded border disabled:opacity-40">Siguiente</button>
        </div>
      )}
    </div>
  )
}
