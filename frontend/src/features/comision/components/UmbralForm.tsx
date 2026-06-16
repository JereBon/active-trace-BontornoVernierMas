// features/comision/components/UmbralForm.tsx
// React Hook Form + Zod — configure passing threshold.
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Spinner } from '@/shared/components/Spinner'
import { configurarUmbral } from '../services/calificacionesService'
import type { UmbralResponse } from '../types'

const schema = z.object({
  umbral_pct: z
    .number({ invalid_type_error: 'El umbral debe ser un número' })
    .int('El umbral debe ser un entero')
    .min(0, 'El umbral debe ser al menos 0')
    .max(100, 'El umbral no puede superar 100'),
  valores_aprobatorios: z.string(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  materiaId: string
  asignacionId: string
  onGuardado?: (result: UmbralResponse) => void
}

export function UmbralForm({ materiaId, asignacionId, onGuardado }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { umbral_pct: 60, valores_aprobatorios: '' },
  })

  const mutation = useMutation<UmbralResponse, Error, FormValues>({
    mutationFn: (values) =>
      configurarUmbral(materiaId, {
        asignacion_id: asignacionId,
        umbral_pct: values.umbral_pct,
        valores_aprobatorios: values.valores_aprobatorios
          ? values.valores_aprobatorios.split(',').map((v) => v.trim()).filter(Boolean)
          : [],
      }),
    onSuccess: (data) => onGuardado?.(data),
  })

  function onSubmit(values: FormValues) {
    mutation.mutate(values)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label
          htmlFor="umbral_pct"
          className="block text-sm font-medium text-gray-700"
        >
          Umbral de aprobación (%)
        </label>
        <input
          id="umbral_pct"
          type="number"
          {...register('umbral_pct', { valueAsNumber: true })}
          className="mt-1 block w-32 rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none"
        />
        {errors.umbral_pct && (
          <p role="alert" className="mt-1 text-xs text-red-600">
            {errors.umbral_pct.message}
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="valores_aprobatorios"
          className="block text-sm font-medium text-gray-700"
        >
          Valores aprobatorios textuales{' '}
          <span className="text-gray-400">(separados por coma, opcional)</span>
        </label>
        <input
          id="valores_aprobatorios"
          type="text"
          placeholder="Aprobado, A, Regular"
          {...register('valores_aprobatorios')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none"
        />
      </div>

      {mutation.error && (
        <p role="alert" className="text-sm text-red-600">
          {mutation.error.message}
        </p>
      )}

      {mutation.isSuccess && (
        <p className="text-sm text-green-600">Umbral guardado correctamente.</p>
      )}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {mutation.isPending && <Spinner />}
        {mutation.isPending ? 'Guardando…' : 'Guardar umbral'}
      </button>
    </form>
  )
}
