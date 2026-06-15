// features/coordinacion/pages/ProgramasPage.tsx
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useProgramas, useCreatePrograma, useDeletePrograma } from '../hooks/useProgramas'
import { useMaterias, useCohortes } from '@/features/admin/hooks/useEstructura'
import type { ProgramaCreate } from '../services/programasService'

const programaSchema = z.object({
  materia_id: z.string().uuid('Seleccioná una materia'),
  cohorte_id: z.preprocess((v) => (v === '' ? null : v), z.string().uuid().nullable().optional()),
  titulo: z.string().min(1, 'El título es requerido'),
  referencia_archivo: z.string().url('URL inválida').nullable().optional().or(z.literal('')),
  vigente: z.boolean(),
})

type ProgramaFormValues = z.infer<typeof programaSchema>

export function ProgramasPage() {
  const [showForm, setShowForm] = useState(false)
  const { data: programas = [], isLoading } = useProgramas()
  const { data: materias = [] } = useMaterias()
  const { data: cohortes = [] } = useCohortes()
  const createPrograma = useCreatePrograma()
  const deletePrograma = useDeletePrograma()

  const { register, handleSubmit, reset, formState: { errors } } = useForm<ProgramaFormValues>({
    resolver: zodResolver(programaSchema),
    defaultValues: { vigente: true, cohorte_id: null, referencia_archivo: null },
  })

  const onSubmit = (data: ProgramaFormValues) => {
    const payload: ProgramaCreate = {
      materia_id: data.materia_id,
      cohorte_id: data.cohorte_id || null,
      titulo: data.titulo,
      referencia_archivo: data.referencia_archivo || null,
      vigente: data.vigente,
    }
    createPrograma.mutate(payload, {
      onSuccess: () => { setShowForm(false); reset() },
    })
  }

  const materiaNombre = (id: string) =>
    materias.find((m) => m.id === id)?.nombre ?? id

  const cohorteLabel = (id: string | null | undefined) => {
    if (!id) return '—'
    const c = cohortes.find((co) => co.id === id)
    return c ? `${c.anio}${c.plan ? ` (${c.plan})` : ''}` : id
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Programas de Materias</h2>
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Nuevo Programa
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Nuevo Programa</h3>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte (opcional)</label>
                <select {...register('cohorte_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white">
                  <option value="">— Sin cohorte —</option>
                  {cohortes.map((c) => <option key={c.id} value={c.id}>{c.anio}{c.plan ? ` (${c.plan})` : ''}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Título *</label>
              <input {...register('titulo')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
              {errors.titulo && <p className="text-red-600 text-xs mt-1">{errors.titulo.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Referencia archivo (URL, opcional)</label>
              <input {...register('referencia_archivo')} type="url" placeholder="https://..." className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
              {errors.referencia_archivo && <p className="text-red-600 text-xs mt-1">{errors.referencia_archivo.message}</p>}
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="vigente" {...register('vigente')} className="rounded" />
              <label htmlFor="vigente" className="text-sm text-gray-700">Vigente</label>
            </div>
            <div className="flex justify-end gap-3">
              <button type="button" onClick={() => { setShowForm(false); reset() }} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded">
                Cancelar
              </button>
              <button type="submit" disabled={createPrograma.isPending} className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50">
                Crear
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {isLoading ? (
          <p className="text-center text-gray-400 py-8">Cargando...</p>
        ) : programas.length === 0 ? (
          <p className="text-center text-gray-400 py-8">No hay programas registrados.</p>
        ) : (
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Título</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Materia</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Cohorte</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Vigente</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Archivo</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {programas.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-900">{p.titulo}</td>
                  <td className="px-4 py-2 text-gray-600">{materiaNombre(p.materia_id)}</td>
                  <td className="px-4 py-2 text-gray-600">{cohorteLabel(p.cohorte_id)}</td>
                  <td className="px-4 py-2">
                    {p.vigente
                      ? <span className="text-green-600 font-medium">Sí</span>
                      : <span className="text-gray-400">No</span>}
                  </td>
                  <td className="px-4 py-2">
                    {p.referencia_archivo
                      ? <a href={p.referencia_archivo} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs">Ver</a>
                      : <span className="text-gray-400">—</span>}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => {
                        if (window.confirm('¿Eliminar este programa?')) {
                          deletePrograma.mutate(p.id)
                        }
                      }}
                      disabled={deletePrograma.isPending}
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
