// features/coordinacion/components/encuentros/EncuentroForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { EncuentroCreate } from '../../types'

const schema = z.object({
  fecha: z.string().min(1, 'La fecha es requerida'),
  tipo: z.enum(['presencial', 'virtual', 'hibrido']),
  cupo_maximo: z.coerce.number().positive().nullable().optional(),
  descripcion: z.string().nullable().optional(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  onSubmit: (data: EncuentroCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

export function EncuentroForm({ onSubmit, onCancel, isLoading }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { fecha: '', tipo: 'presencial', cupo_maximo: null, descripcion: null },
  })

  const onValid = (data: FormValues) => {
    onSubmit({
      fecha: data.fecha,
      tipo: data.tipo,
      cupo_maximo: data.cupo_maximo ?? null,
      descripcion: data.descripcion ?? null,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
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
        <label htmlFor="tipo" className="block text-sm font-medium text-gray-700 mb-1">
          Tipo
        </label>
        <select
          id="tipo"
          {...register('tipo')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
        >
          <option value="presencial">Presencial</option>
          <option value="virtual">Virtual</option>
          <option value="hibrido">Híbrido</option>
        </select>
      </div>

      <div>
        <label htmlFor="cupo_maximo" className="block text-sm font-medium text-gray-700 mb-1">
          Cupo máximo
        </label>
        <input
          id="cupo_maximo"
          type="number"
          {...register('cupo_maximo')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="Sin límite"
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
          Guardar
        </button>
      </div>
    </form>
  )
}
