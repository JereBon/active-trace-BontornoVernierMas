// features/coordinacion/components/coloquios/ColoquioForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { ColoquioCreate } from '../../types'

const schema = z.object({
  materia_id: z.string().min(1, 'La materia es requerida'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  descripcion: z.string().nullable().optional(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  onSubmit: (data: ColoquioCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

export function ColoquioForm({ onSubmit, onCancel, isLoading }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { materia_id: '', fecha: '', descripcion: null },
  })

  const onValid = (data: FormValues) => {
    onSubmit({
      materia_id: data.materia_id,
      fecha: data.fecha,
      descripcion: data.descripcion ?? null,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      <div>
        <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700 mb-1">
          Materia ID
        </label>
        <input
          id="materia_id"
          {...register('materia_id')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="ID de la materia"
        />
        {errors.materia_id && (
          <p className="text-red-600 text-xs mt-1">{errors.materia_id.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="fecha" className="block text-sm font-medium text-gray-700 mb-1">
          Fecha
        </label>
        <input
          id="fecha"
          type="datetime-local"
          {...register('fecha')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
        />
        {errors.fecha && <p className="text-red-600 text-xs mt-1">{errors.fecha.message}</p>}
      </div>

      <div>
        <label htmlFor="descripcion" className="block text-sm font-medium text-gray-700 mb-1">
          Descripción
        </label>
        <textarea
          id="descripcion"
          {...register('descripcion')}
          rows={3}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="Descripción opcional"
        />
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Crear Convocatoria
        </button>
      </div>
    </form>
  )
}
