import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  useFechas,
  useCreateFecha,
  useDeleteFecha,
} from '@/features/coordinacion/hooks/useFechas'
import { useMaterias } from '@/features/admin/hooks/useEstructura'
import { useCohortes } from '@/features/admin/hooks/useEstructura'
import { Spinner } from '@/shared/components/Spinner'
import type { FechaAcademicaCreate, TipoEvaluacion } from '@/features/coordinacion/services/fechasService'
import type { Cohorte } from '@/features/admin/types'

const TIPOS: { value: TipoEvaluacion; label: string }[] = [
  { value: 'PARCIAL', label: 'Parcial' },
  { value: 'TP', label: 'Trabajo Práctico' },
  { value: 'COLOQUIO', label: 'Coloquio' },
  { value: 'RECUPERATORIO', label: 'Recuperatorio' },
]

const createSchema = z
  .object({
    materia_id: z.string().min(1, 'Seleccioná una materia'),
    cohorte_id: z.string().min(1, 'Seleccioná una cohorte'),
    tipo: z.string().min(1, 'Seleccioná un tipo'),
    numero: z.coerce.number().int().min(1, 'Mínimo 1'),
    periodo: z.string().min(1, 'El período es requerido'),
    fecha: z.string().min(1, 'La fecha es requerida'),
    titulo: z.string().min(1, 'El título es requerido'),
  })
  .strict()

type CreateFormValues = z.infer<typeof createSchema>

export function FechasPage() {
  const [selectedMateria, setSelectedMateria] = useState<string | undefined>()
  const [showForm, setShowForm] = useState(false)

  const { data: fechas = [], isLoading } = useFechas(selectedMateria)
  const { data: materias = [] } = useMaterias()
  const { data: cohortes = [] } = useCohortes()
  const createFecha = useCreateFecha()
  const deleteFecha = useDeleteFecha()

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CreateFormValues>({
    resolver: zodResolver(createSchema),
  })

  const watchedMateriaId = watch('materia_id')

  const onSubmit = async (values: CreateFormValues) => {
    const payload: FechaAcademicaCreate = {
      materia_id: values.materia_id,
      cohorte_id: values.cohorte_id,
      tipo: values.tipo as TipoEvaluacion,
      numero: values.numero,
      periodo: values.periodo,
      fecha: values.fecha,
      titulo: values.titulo,
    }
    await createFecha.mutateAsync(payload)
    reset()
    setShowForm(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">
          Fechas Académicas
        </h2>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Nueva fecha
        </button>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">
          Filtrar por materia:
        </label>
        <select
          value={selectedMateria ?? ''}
          onChange={(e) =>
            setSelectedMateria(e.target.value || undefined)
          }
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
        >
          <option value="">Todas las materias</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>
              {m.nombre} ({m.codigo})
            </option>
          ))}
        </select>
      </div>

      {showForm && (
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-medium text-gray-900">
            Crear fecha académica
          </h3>
          <form
            onSubmit={handleSubmit(onSubmit)}
            noValidate
            className="space-y-4"
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
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
                      {m.nombre}
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
                  Cohorte
                </label>
                <select
                  {...register('cohorte_id')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                >
                  <option value="">Seleccionar…</option>
                  {cohortes
                    .filter(
                      (c: Cohorte) =>
                        !watchedMateriaId ||
                        c.carrera_id ===
                          materias.find(
                            (m) => m.id === watchedMateriaId,
                          )?.id,
                    )
                    .map((c: Cohorte) => (
                      <option key={c.id} value={c.id}>
                        {c.plan ?? `Cohorte ${c.anio}`}
                      </option>
                    ))}
                </select>
                {errors.cohorte_id && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.cohorte_id.message}
                  </p>
                )}
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Tipo
                </label>
                <select
                  {...register('tipo')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                >
                  <option value="">Seleccionar…</option>
                  {TIPOS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
                {errors.tipo && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.tipo.message}
                  </p>
                )}
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Número
                </label>
                <input
                  type="number"
                  min={1}
                  {...register('numero')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
                {errors.numero && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.numero.message}
                  </p>
                )}
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Período
                </label>
                <input
                  type="text"
                  placeholder="ej: 2026-1"
                  {...register('periodo')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
                {errors.periodo && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.periodo.message}
                  </p>
                )}
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Fecha
                </label>
                <input
                  type="date"
                  {...register('fecha')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
                {errors.fecha && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.fecha.message}
                  </p>
                )}
              </div>

              <div className="sm:col-span-3">
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
                  Tipo
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  N°
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Período
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Fecha
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Materia
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase text-gray-500">
                  Acción
                </th>
              </tr>
            </thead>
            <tbody>
              {fechas.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-8 text-center text-sm text-gray-400"
                  >
                    No hay fechas registradas{selectedMateria ? ' para esta materia' : ''}.
                  </td>
                </tr>
              ) : (
                fechas.map((f) => {
                  const materia = materias.find(
                    (m) => m.id === f.materia_id,
                  )
                  return (
                    <tr
                      key={f.id}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {f.titulo}
                      </td>
                      <td className="px-4 py-3">
                        <span className={TIPO_CLASSES[f.tipo] ?? ''}>
                          {f.tipo}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {f.numero}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {f.periodo}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {new Date(f.fecha).toLocaleDateString('es-AR')}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {materia?.nombre ?? f.materia_id.slice(0, 8)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <button
                          onClick={() => {
                            if (
                              window.confirm(
                                `¿Eliminar "${f.titulo}"?`,
                              )
                            ) {
                              deleteFecha.mutate(f.id)
                            }
                          }}
                          disabled={deleteFecha.isPending}
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

const TIPO_CLASSES: Record<string, string> = {
  PARCIAL: 'inline-flex rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700',
  TP: 'inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700',
  COLOQUIO: 'inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700',
  RECUPERATORIO: 'inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700',
}
