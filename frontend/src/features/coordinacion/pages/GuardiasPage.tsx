import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { useGuardias, useCreateGuardia } from '../hooks/useGuardias'
import { DIAS_SEMANA, ESTADOS_GUARDIA, exportarGuardias } from '../services/guardiasService'
import type { GuardiaCreate, GuardiaFilter } from '../services/guardiasService'
import { getUsuarios } from '../services/equiposService'
import { getCarreras, getCohortes, getMaterias } from '@/features/admin/services/estructuraService'
import { useEquipos } from '../hooks/useEquipos'

const schema = z.object({
  asignacion_id: z.string().uuid('Seleccioná una asignación'),
  materia_id: z.string().uuid('Seleccioná una materia'),
  carrera_id: z.string().uuid('Seleccioná una carrera'),
  cohorte_id: z.string().uuid('Seleccioná un cohorte'),
  dia: z.enum(DIAS_SEMANA, { required_error: 'El día es requerido' }),
  horario: z.string().min(1, 'El horario es requerido').max(20),
  estado: z.enum(ESTADOS_GUARDIA).optional(),
  comentarios: z.string().nullable().optional(),
})

type FormValues = z.infer<typeof schema>

const ESTADO_COLORS: Record<string, string> = {
  Pendiente: 'bg-yellow-50 text-yellow-700',
  Realizada: 'bg-green-50 text-green-700',
  Cancelada: 'bg-red-50 text-red-700',
}

export function GuardiasPage() {
  const [showForm, setShowForm] = useState(false)
  const [materiaFilter, setMateriaFilter] = useState('')
  const [carreraFilter, setCarreraFilter] = useState('')
  const [cohorteFilter, setCohorteFilter] = useState('')
  const [estadoFilter, setEstadoFilter] = useState('')

  const filters: GuardiaFilter = {
    ...(materiaFilter ? { materia_id: materiaFilter } : {}),
    ...(carreraFilter ? { carrera_id: carreraFilter } : {}),
    ...(cohorteFilter ? { cohorte_id: cohorteFilter } : {}),
    ...(estadoFilter ? { estado: estadoFilter } : {}),
  }

  const { data: guardias = [], isLoading } = useGuardias(filters)
  const createGuardia = useCreateGuardia()

  const { data: asignaciones = [] } = useEquipos()
  const { data: usuarios = [] } = useQuery({ queryKey: ['usuarios'], queryFn: getUsuarios })
  const { data: materias = [] } = useQuery({ queryKey: ['materias'], queryFn: getMaterias })
  const { data: carreras = [] } = useQuery({ queryKey: ['carreras'], queryFn: getCarreras })
  const { data: cohortes = [] } = useQuery({ queryKey: ['cohortes-all'], queryFn: () => getCohortes() })

  const userMap = Object.fromEntries(usuarios.map((u) => [u.id, `${u.nombre}${u.apellidos ? ' ' + u.apellidos : ''}`]))
  const materiaMap = Object.fromEntries(materias.map((m) => [m.id, m.nombre]))
  const carreraMap = Object.fromEntries(carreras.map((c) => [c.id, c.nombre]))
  const cohorteMap = Object.fromEntries(cohortes.map((c) => [c.id, c.nombre]))

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { dia: 'Lunes', estado: 'Pendiente' },
  })

  const selectedMateria = watch('materia_id')
  const selectedCarrera = watch('carrera_id')
  const selectedCohorte = watch('cohorte_id')

  const asignacionesFiltradas = asignaciones.filter((a) => {
    if (selectedMateria && a.materia_id !== selectedMateria) return false
    if (selectedCarrera && a.carrera_id !== selectedCarrera) return false
    if (selectedCohorte && a.cohorte_id !== selectedCohorte) return false
    return true
  })

  const onValid = (data: FormValues) => {
    createGuardia.mutate(data as GuardiaCreate, {
      onSuccess: () => { reset(); setShowForm(false) },
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Guardias</h2>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showForm ? 'Cerrar' : 'Registrar Guardia'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Nueva Guardia</h3>
          <form onSubmit={handleSubmit(onValid)} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="g-materia" className="block text-sm font-medium text-gray-700 mb-1">Materia</label>
                <select id="g-materia" {...register('materia_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                  <option value="">Seleccioná materia</option>
                  {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
                </select>
                {errors.materia_id && <p className="text-red-600 text-xs mt-1">{errors.materia_id.message}</p>}
              </div>
              <div>
                <label htmlFor="g-carrera" className="block text-sm font-medium text-gray-700 mb-1">Carrera</label>
                <select id="g-carrera" {...register('carrera_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                  <option value="">Seleccioná carrera</option>
                  {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                </select>
                {errors.carrera_id && <p className="text-red-600 text-xs mt-1">{errors.carrera_id.message}</p>}
              </div>
              <div>
                <label htmlFor="g-cohorte" className="block text-sm font-medium text-gray-700 mb-1">Cohorte</label>
                <select id="g-cohorte" {...register('cohorte_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                  <option value="">Seleccioná cohorte</option>
                  {cohortes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                </select>
                {errors.cohorte_id && <p className="text-red-600 text-xs mt-1">{errors.cohorte_id.message}</p>}
              </div>
            </div>

            <div>
              <label htmlFor="g-asignacion" className="block text-sm font-medium text-gray-700 mb-1">Asignación (docente)</label>
              <select id="g-asignacion" {...register('asignacion_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                <option value="">Primero seleccioná materia/carrera/cohorte</option>
                {asignacionesFiltradas.map((a) => (
                  <option key={a.id} value={a.id}>
                    {userMap[a.usuario_id] ?? a.usuario_id.slice(0, 8)} — {a.rol}
                  </option>
                ))}
              </select>
              {errors.asignacion_id && <p className="text-red-600 text-xs mt-1">{errors.asignacion_id.message}</p>}
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="g-dia" className="block text-sm font-medium text-gray-700 mb-1">Día</label>
                <select id="g-dia" {...register('dia')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                  {DIAS_SEMANA.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="g-horario" className="block text-sm font-medium text-gray-700 mb-1">Horario</label>
                <input id="g-horario" {...register('horario')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" placeholder="14:00-15:30" />
                {errors.horario && <p className="text-red-600 text-xs mt-1">{errors.horario.message}</p>}
              </div>
              <div>
                <label htmlFor="g-estado" className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                <select id="g-estado" {...register('estado')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                  {ESTADOS_GUARDIA.map((e) => <option key={e} value={e}>{e}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="g-comentarios" className="block text-sm font-medium text-gray-700 mb-1">Comentarios (opcional)</label>
              <textarea id="g-comentarios" {...register('comentarios')} rows={2} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => { reset(); setShowForm(false) }} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50">Cancelar</button>
              <button type="submit" disabled={createGuardia.isPending} className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50">
                {createGuardia.isPending ? 'Guardando…' : 'Guardar'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <select value={materiaFilter} onChange={(e) => setMateriaFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1 text-sm" aria-label="Filtrar materia">
            <option value="">Todas las materias</option>
            {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
          </select>
          <select value={carreraFilter} onChange={(e) => setCarreraFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1 text-sm" aria-label="Filtrar carrera">
            <option value="">Todas las carreras</option>
            {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
          <select value={cohorteFilter} onChange={(e) => setCohorteFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1 text-sm" aria-label="Filtrar cohorte">
            <option value="">Todos los cohortes</option>
            {cohortes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
          <select value={estadoFilter} onChange={(e) => setEstadoFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1 text-sm" aria-label="Filtrar estado">
            <option value="">Todos los estados</option>
            {ESTADOS_GUARDIA.map((e) => <option key={e} value={e}>{e}</option>)}
          </select>
          <button
            onClick={() => exportarGuardias(filters)}
            disabled={guardias.length === 0}
            className="ml-auto px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40"
          >
            Exportar CSV
          </button>
        </div>

        {isLoading ? (
          <p className="text-gray-500 text-sm">Cargando guardias…</p>
        ) : guardias.length === 0 ? (
          <p className="text-center text-gray-400 py-8">No hay guardias registradas.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Materia</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Carrera</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Cohorte</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Docente</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Día</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Horario</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Comentarios</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {guardias.map((g) => (
                  <tr key={g.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-gray-700">{materiaMap[g.materia_id] ?? '—'}</td>
                    <td className="px-4 py-2 text-gray-700">{carreraMap[g.carrera_id] ?? '—'}</td>
                    <td className="px-4 py-2 text-gray-700">{cohorteMap[g.cohorte_id] ?? '—'}</td>
                    <td className="px-4 py-2 text-gray-700">
                      {userMap[asignaciones.find((a) => a.id === g.asignacion_id)?.usuario_id ?? ''] ?? '—'}
                    </td>
                    <td className="px-4 py-2 text-gray-600">{g.dia}</td>
                    <td className="px-4 py-2 font-mono text-xs text-gray-600">{g.horario}</td>
                    <td className="px-4 py-2">
                      <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${ESTADO_COLORS[g.estado] ?? 'bg-gray-100 text-gray-600'}`}>{g.estado}</span>
                    </td>
                    <td className="px-4 py-2 text-xs text-gray-500">{g.comentarios ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-gray-400 mt-2">{guardias.length} registros</p>
          </div>
        )}
      </div>
    </div>
  )
}
