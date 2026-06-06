// features/coordinacion/components/avisos/AvisoForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { AvisoCreate } from '../../types'

const schema = z.object({
  titulo: z.string().min(1, 'El título es requerido'),
  cuerpo: z.string().min(1, 'El cuerpo es requerido'),
  scope: z.enum(['todos', 'coordinadores', 'profesores', 'alumnos']),
  severidad: z.enum(['info', 'advertencia', 'critico']),
  vigencia_hasta: z.string().nullable().optional(),
  requiere_ack: z.boolean(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  onSubmit: (data: AvisoCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

export function AvisoForm({ onSubmit, onCancel, isLoading }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      titulo: '',
      cuerpo: '',
      scope: 'todos',
      severidad: 'info',
      vigencia_hasta: null,
      requiere_ack: false,
    },
  })

  const onValid = (data: FormValues) => {
    onSubmit({
      titulo: data.titulo,
      cuerpo: data.cuerpo,
      scope: data.scope,
      severidad: data.severidad,
      vigencia_hasta: data.vigencia_hasta ?? null,
      requiere_ack: data.requiere_ack,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      <div>
        <label htmlFor="titulo" className="block text-sm font-medium text-gray-700 mb-1">
          Título
        </label>
        <input
          id="titulo"
          {...register('titulo')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="Título del aviso"
        />
        {errors.titulo && (
          <p className="text-red-600 text-xs mt-1">{errors.titulo.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="cuerpo" className="block text-sm font-medium text-gray-700 mb-1">
          Cuerpo
        </label>
        <textarea
          id="cuerpo"
          {...register('cuerpo')}
          rows={4}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="Contenido del aviso"
        />
        {errors.cuerpo && (
          <p className="text-red-600 text-xs mt-1">{errors.cuerpo.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="scope" className="block text-sm font-medium text-gray-700 mb-1">
            Scope
          </label>
          <select
            id="scope"
            {...register('scope')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          >
            <option value="todos">Todos</option>
            <option value="coordinadores">Coordinadores</option>
            <option value="profesores">Profesores</option>
            <option value="alumnos">Alumnos</option>
          </select>
        </div>

        <div>
          <label htmlFor="severidad" className="block text-sm font-medium text-gray-700 mb-1">
            Severidad
          </label>
          <select
            id="severidad"
            {...register('severidad')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          >
            <option value="info">Info</option>
            <option value="advertencia">Advertencia</option>
            <option value="critico">Crítico</option>
          </select>
        </div>
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

      <div className="flex items-center gap-2">
        <input
          id="requiere_ack"
          type="checkbox"
          {...register('requiere_ack')}
          className="h-4 w-4 text-blue-600"
        />
        <label htmlFor="requiere_ack" className="text-sm text-gray-700">
          Requiere confirmación (Ack)
        </label>
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
          Publicar
        </button>
      </div>
    </form>
  )
}
