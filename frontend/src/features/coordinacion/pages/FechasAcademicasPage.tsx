// features/coordinacion/pages/FechasAcademicasPage.tsx
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useFechas, useCreateFecha, useDeleteFecha } from '../hooks/useFechas'
import { useMaterias, useCohortes } from '@/features/admin/hooks/useEstructura'
import type { FechaCreate, FechaTipo } from '../services/fechasService'

const TIPOS: FechaTipo[] = ['PARCIAL', 'TP', 'COLOQUIO', 'RECUPERATORIO']

const fechaSchema = z.object({
  materia_id: z.string().uuid('Seleccioná una materia'),
  cohorte_id: z.string().uuid('Seleccioná una cohorte'),
  tipo: z.enum(['PARCIAL', 'TP', 'COLOQUIO', 'RECUPERATORIO']),
  numero: z.coerce.number().int().min(1, 'Mínimo 1'),
  periodo: z.string().min(1, 'El período es requerido'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  titulo: z.string().min(1, 'El título es requerido'),
})

type FechaFormValues = z.infer<typeof fechaSchema>

export function FechasAcademicasPage() {
  const [showForm, setShowForm] = useState(false)
  const [filtroMateria, setFiltroMateria] = useState<string | undefined>(undefined)

  const { data: fechas = [], isLoading } = useFechas(filtroMateria)
  const { data: materias = [] } = useMaterias()
  const { data: cohortes = [] } = useCohortes()
  const createFecha = useCreateFecha()
  const deleteFecha = useDeleteFecha()

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FechaFormValues>({
    resolver: zodResolver(fechaSchema),
    defaultValues: { tipo: 'PARCIAL', numero: 1 },
  })

  const onSubmit = (data: FechaFormValues) => {
    const payload: FechaCreate = {
      materia_id: data.materia_id,
      cohorte_id: data.cohorte_id,
      tipo: data.tipo,
      numero: data.numero,
      periodo: data.periodo,
      fecha: data.fecha,
      titulo: data.titulo,
    }
    createFecha.mutate(payload, {
      onSuccess: () => { setShowForm(false); reset() },
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Fechas Académicas</h2>
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Nueva Fecha
        </button>
      </div>

      {/* Filtro por materia */}
      <div className="flex items-center gap-3">
        <label className="text-sm text-gray-600">Filtrar por materia:</label>
        <select
          value={filtroMateria ?? ''}
          onChange={(e) => setFiltroMateria(e.target.value || undefined)}
          className="border border-gray-300 rounded px-2 py-1 text-sm bg-white"
        >
          <option value="">Todas</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>{m.nombre}</option>
          ))}
        </select>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Nueva Fecha Académica</h3>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Materia *</label>
                <select {...register('materia_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white">
                  <option value="">— Seleccioná —</option>
                  {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
                </select>
                {errors.materia_id && <p className="text-red-600 text-xs mt-1">{errors.materia_id.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte *</label>
                <select {...register('cohorte_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white">
                  <option value="">— Seleccioná —</option>
                  {cohortes.map((c) => <option key={c.id} value={c.id}>{c.anio}{c.plan ? ` (${c.plan})` : ''}</option>)}
                </select>
                {errors.cohorte_id && <p className="text-red-600 text-xs mt-1">{errors.cohorte_id.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo *</label>
                <select {...register('tipo')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white">
                  {TIPOS.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Número *</label>
                <input type="number" {...register('numero')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
                {errors.numero && <p className="text-red-600 text-xs mt-1">{errors.numero.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Período *</label>
                <input {...register('periodo')} placeholder="ej. 2025-1C" className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
                {errors.periodo && <p className="text-red-600 text-xs mt-1">{errors.periodo.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fecha *</label>
                <input type="date" {...register('fecha')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
                {errors.fecha && <p className="text-red-600 text-xs mt-1">{errors.fecha.message}</p>}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Título *</label>
              <input {...register('titulo')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
              {errors.titulo && <p className="text-red-600 text-xs mt-1">{errors.titulo.message}</p>}
            </div>
            <div className="flex justify-end gap-3">
              <button type="button" onClick={() => { setShowForm(false); reset() }} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded">
                Cancelar
              </button>
              <button type="submit" disabled={createFecha.isPending} className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50">
                Crear
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {isLoading ? (
          <p className="text-center text-gray-400 py-8">Cargando...</p>
        ) : fechas.length === 0 ? (
          <p className="text-center text-gray-400 py-8">No hay fechas registradas.</p>
        ) : (
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Título</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Materia</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Tipo</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Nro</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Período</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Fecha</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {fechas.map((f) => (
                <tr key={f.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-900">{f.titulo}</td>
                  <td className="px-4 py-2 text-gray-600">
                    {materias.find((m) => m.id === f.materia_id)?.nombre ?? f.materia_id.slice(0, 8) + '…'}
                  </td>
                  <td className="px-4 py-2 text-gray-600">{f.tipo}</td>
                  <td className="px-4 py-2 text-gray-600">{f.numero}</td>
                  <td className="px-4 py-2 text-gray-600">{f.periodo}</td>
                  <td className="px-4 py-2 text-gray-600">{f.fecha}</td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => {
                        if (window.confirm('¿Eliminar esta fecha académica?')) {
                          deleteFecha.mutate(f.id)
                        }
                      }}
                      disabled={deleteFecha.isPending}
                      className="text-red-600 hover:text-red-800 text-xs disabled:opacity-50"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
