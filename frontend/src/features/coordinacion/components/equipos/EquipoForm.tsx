// features/coordinacion/components/equipos/EquipoForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { EquipoDocente, EquipoDocenteCreate } from '../../types'

const ROLES = ['PROFESOR', 'TUTOR', 'COORDINADOR', 'NEXO', 'ADMIN', 'FINANZAS'] as const

const schema = z.object({
  usuario_id: z.string().uuid('Debe ser un UUID válido'),
  rol: z.enum(ROLES),
  materia_id: z.string().uuid('Debe ser un UUID válido').optional().or(z.literal('')),
  desde: z.string().min(1, 'La fecha de inicio es requerida'),
  hasta: z.string().optional().or(z.literal('')),
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
      usuario_id: defaultValues?.usuario_id ?? '',
      rol: (defaultValues?.rol as typeof ROLES[number]) ?? 'PROFESOR',
      materia_id: defaultValues?.materia_id ?? '',
      desde: defaultValues?.desde ?? '',
      hasta: defaultValues?.hasta ?? '',
    },
  })

  const onValid = (data: FormValues) => {
    onSubmit({
      usuario_id: data.usuario_id,
      rol: data.rol,
      materia_id: data.materia_id || null,
      desde: data.desde,
      hasta: data.hasta || null,
      comisiones: [],
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      <div>
        <label htmlFor="usuario_id" className="block text-sm font-medium text-gray-700 mb-1">
          Usuario ID <span className="text-red-500">*</span>
        </label>
        <input
          id="usuario_id"
          {...register('usuario_id')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="UUID del usuario"
        />
        {errors.usuario_id && (
          <p className="text-red-600 text-xs mt-1">{errors.usuario_id.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="rol" className="block text-sm font-medium text-gray-700 mb-1">
          Rol <span className="text-red-500">*</span>
        </label>
        <select
          id="rol"
          {...register('rol')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700 mb-1">
          Materia ID
        </label>
        <input
          id="materia_id"
          {...register('materia_id')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="UUID de la materia (opcional)"
        />
        {errors.materia_id && (
          <p className="text-red-600 text-xs mt-1">{errors.materia_id.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="desde" className="block text-sm font-medium text-gray-700 mb-1">
            Desde <span className="text-red-500">*</span>
          </label>
          <input
            id="desde"
            type="date"
            {...register('desde')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          {errors.desde && (
            <p className="text-red-600 text-xs mt-1">{errors.desde.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="hasta" className="block text-sm font-medium text-gray-700 mb-1">
            Hasta
          </label>
          <input
            id="hasta"
            type="date"
            {...register('hasta')}
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
