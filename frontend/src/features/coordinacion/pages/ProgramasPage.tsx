import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  useProgramas,
  useCreatePrograma,
  useDeletePrograma,
} from '@/features/coordinacion/hooks/useProgramas'
import { useMaterias } from '@/features/admin/hooks/useEstructura'
import { Spinner } from '@/shared/components/Spinner'
import type { ProgramaMateriaCreate } from '@/features/coordinacion/services/programasService'

const createSchema = z
  .object({
    materia_id: z.string().min(1, 'Seleccioná una materia'),
    titulo: z.string().min(1, 'El título es requerido'),
    referencia_archivo: z.string().optional(),
    vigente: z.boolean(),
  })
  .strict()

type CreateFormValues = z.infer<typeof createSchema>

export function ProgramasPage() {
  const { data: programas = [], isLoading } = useProgramas()
  const { data: materias = [] } = useMaterias()
  const createPrograma = useCreatePrograma()
  const deletePrograma = useDeletePrograma()

  const [showForm, setShowForm] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateFormValues>({
    resolver: zodResolver(createSchema),
    defaultValues: { vigente: true },
  })

  const onSubmit = async (values: CreateFormValues) => {
    const payload: ProgramaMateriaCreate = {
      materia_id: values.materia_id,
      titulo: values.titulo,
      referencia_archivo: values.referencia_archivo || null,
      vigente: values.vigente,
    }
    await createPrograma.mutateAsync(payload)
    reset()
    setShowForm(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">
          Programas de Materia
        </h2>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Nuevo programa
        </button>
      </div>

      {showForm && (
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-medium text-gray-900">
            Crear programa
          </h3>
          <form
            onSubmit={handleSubmit(onSubmit)}
            noValidate
            className="space-y-4"
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Materia
                </label>
                <select
                  {...register('materia_id')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                >
                  <option value="">Seleccionar…</option>
                  {materias.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nombre} ({m.codigo})
                    </option>
                  ))}
                </select>
                {errors.materia_id && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.materia_id.message}
                  </p>
                )}
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Título
                </label>
                <input
                  type="text"
                  {...register('titulo')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
                {errors.titulo && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.titulo.message}
                  </p>
                )}
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  URL del archivo (opcional)
                </label>
                <input
                  type="text"
                  {...register('referencia_archivo')}
                  placeholder="https://..."
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="vigente"
                  {...register('vigente')}
                  className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="vigente" className="text-sm text-gray-700">
                  Vigente
                </label>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
              >
                {isSubmitting ? <Spinner size="sm" /> : null}
                {isSubmitting ? 'Creando…' : 'Crear'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-left">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Título
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Materia
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Vigente
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Archivo
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Creado
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Acción
                </th>
              </tr>
            </thead>
            <tbody>
              {programas.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-sm text-gray-400"
                  >
                    No hay programas registrados.
                  </td>
                </tr>
              ) : (
                programas.map((p) => {
                  const materia = materias.find(
                    (m) => m.id === p.materia_id,
                  )
                  return (
                    <tr
                      key={p.id}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {p.titulo}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {materia?.nombre ?? p.materia_id.slice(0, 8)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            p.vigente
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {p.vigente ? 'Sí' : 'No'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {p.referencia_archivo ? (
                          <a
                            href={p.referencia_archivo}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-brand-600 hover:text-brand-700"
                          >
                            Ver archivo
                          </a>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {new Date(p.created_at).toLocaleDateString('es-AR')}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <button
                          onClick={() => {
                            if (
                              window.confirm(
                                `¿Eliminar el programa "${p.titulo}"?`,
                              )
                            ) {
                              deletePrograma.mutate(p.id)
                            }
                          }}
                          disabled={deletePrograma.isPending}
                          className="rounded bg-red-500 px-2 py-1 text-xs font-medium text-white hover:bg-red-600 disabled:opacity-50"
                        >
                          Eliminar
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
