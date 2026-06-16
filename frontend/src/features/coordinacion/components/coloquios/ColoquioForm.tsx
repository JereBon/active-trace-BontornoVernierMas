// features/coordinacion/components/coloquios/ColoquioForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCohortes, useMaterias } from '@/features/admin/hooks/useEstructura'
import type { ColoquioCreate } from '../../types'

const TIPOS = ['Parcial', 'TP', 'Coloquio', 'Recuperatorio'] as const

const schema = z.object({
  materia_id: z.string().uuid('Seleccioná una materia'),
  cohorte_id: z.string().uuid('Seleccioná una cohorte'),
  tipo: z.enum(TIPOS).default('Coloquio'),
  instancia: z.string().min(1, 'La instancia es requerida'),
  dias_disponibles: z.coerce.number().int().min(1, 'Mínimo 1 día'),
  cupos_disponibles: z.coerce.number().int().min(1, 'Mínimo 1 cupo'),
})

type FormValues = z.infer<typeof schema>

interface Props {
  onSubmit: (data: ColoquioCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

export function ColoquioForm({ onSubmit, onCancel, isLoading }: Props) {
  const { data: materias = [] } = useMaterias()
  const { data: cohortes = [] } = useCohortes()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { tipo: 'Coloquio', dias_disponibles: 7, cupos_disponibles: 10 },
  })

  const onValid = (data: FormValues) => {
    onSubmit({
      materia_id: data.materia_id,
      cohorte_id: data.cohorte_id,
      tipo: data.tipo,
      instancia: data.instancia,
      dias_disponibles: data.dias_disponibles,
      cupos_disponibles: data.cupos_disponibles,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700 mb-1">
            Materia <span className="text-red-500">*</span>
          </label>
          <select
            id="materia_id"
            {...register('materia_id')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
          >
            <option value="">— Seleccioná una materia —</option>
            {materias.map((m) => (
              <option key={m.id} value={m.id}>{m.nombre} ({m.codigo})</option>
            ))}
          </select>
          {errors.materia_id && <p className="text-red-600 text-xs mt-1">{errors.materia_id.message}</p>}
        </div>
        <div>
          <label htmlFor="cohorte_id" className="block text-sm font-medium text-gray-700 mb-1">
            Cohorte <span className="text-red-500">*</span>
          </label>
          <select
            id="cohorte_id"
            {...register('cohorte_id')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
          >
            <option value="">— Seleccioná una cohorte —</option>
            {cohortes.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre ?? c.anio} — {c.carrera_nombre ?? c.carrera_id}</option>
            ))}
          </select>
          {errors.cohorte_id && <p className="text-red-600 text-xs mt-1">{errors.cohorte_id.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="tipo" className="block text-sm font-medium text-gray-700 mb-1">
            Tipo
          </label>
          <select id="tipo" {...register('tipo')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
            {TIPOS.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="instancia" className="block text-sm font-medium text-gray-700 mb-1">
            Instancia <span className="text-red-500">*</span>
          </label>
          <input
            id="instancia"
            {...register('instancia')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            placeholder="Ej: Coloquio Final"
          />
          {errors.instancia && <p className="text-red-600 text-xs mt-1">{errors.instancia.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="dias_disponibles" className="block text-sm font-medium text-gray-700 mb-1">
            Días de inscripción <span className="text-red-500">*</span>
          </label>
          <input
            id="dias_disponibles"
            type="number"
            min="1"
            {...register('dias_disponibles')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          {errors.dias_disponibles && <p className="text-red-600 text-xs mt-1">{errors.dias_disponibles.message}</p>}
        </div>
        <div>
          <label htmlFor="cupos_disponibles" className="block text-sm font-medium text-gray-700 mb-1">
            Cupos <span className="text-red-500">*</span>
          </label>
          <input
            id="cupos_disponibles"
            type="number"
            min="1"
            {...register('cupos_disponibles')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          {errors.cupos_disponibles && <p className="text-red-600 text-xs mt-1">{errors.cupos_disponibles.message}</p>}
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
          Crear Convocatoria
        </button>
      </div>
    </form>
  )
}
