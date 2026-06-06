// features/coordinacion/components/equipos/EquipoForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { EquipoDocente, EquipoDocenteCreate } from '../../types'

const schema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido'),
  descripcion: z.string().nullable().optional(),
  vigencia_desde: z.string().nullable().optional(),
  vigencia_hasta: z.string().nullable().optional(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  defaultValues?: Partial<EquipoDocente>
  onSubmit: (data: EquipoDocenteCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

export function EquipoForm({ defaultValues, onSubmit, onCancel, isLoading }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      nombre: defaultValues?.nombre ?? '',
      descripcion: defaultValues?.descripcion ?? null,
      vigencia_desde: defaultValues?.vigencia_desde ?? null,
      vigencia_hasta: defaultValues?.vigencia_hasta ?? null,
    },
  })

  const onValid = (data: FormValues) => {
    onSubmit({
      nombre: data.nombre,
      descripcion: data.descripcion ?? null,
      vigencia_desde: data.vigencia_desde ?? null,
      vigencia_hasta: data.vigencia_hasta ?? null,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      <div>
        <label htmlFor="nombre" className="block text-sm font-medium text-gray-700 mb-1">
          Nombre
        </label>
        <input
          id="nombre"
          {...register('nombre')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Nombre del equipo"
        />
        {errors.nombre && (
          <p className="text-red-600 text-xs mt-1">{errors.nombre.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="descripcion" className="block text-sm font-medium text-gray-700 mb-1">
          Descripción
        </label>
        <textarea
          id="descripcion"
          {...register('descripcion')}
          rows={3}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Descripción opcional"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="vigencia_desde" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia desde
          </label>
          <input
            id="vigencia_desde"
            type="date"
            {...register('vigencia_desde')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="vigencia_hasta" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia hasta
          </label>
          <input
            id="vigencia_hasta"
            type="date"
            {...register('vigencia_hasta')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
        </div>
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
          Guardar
        </button>
      </div>
    </form>
  )
}
