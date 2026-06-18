import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { getCarreras, getCohortes, getMaterias } from '@/features/admin/services/estructuraService'

const schema = z.object({
  materia_id: z.string().uuid('Seleccioná una materia'),
  carrera_id: z.string().uuid('Seleccioná una carrera'),
  origen_cohorte_id: z.string().uuid('Seleccioná el cohorte origen'),
  destino_cohorte_id: z.string().uuid('Seleccioná el cohorte destino'),
  desde: z.string().min(1, 'La fecha de inicio es requerida'),
  hasta: z.string().nullable().optional(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  onSubmit: (data: FormValues) => void
  onCancel: () => void
  isLoading?: boolean
}

export function ClonarEquipoModal({ onSubmit, onCancel, isLoading }: Props) {
  const { data: materias = [] } = useQuery({ queryKey: ['materias'], queryFn: getMaterias })
  const { data: carreras = [] } = useQuery({ queryKey: ['carreras'], queryFn: getCarreras })
  const { data: cohortes = [] } = useQuery({ queryKey: ['cohortes-all'], queryFn: () => getCohortes() })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { materia_id: '', carrera_id: '', origen_cohorte_id: '', destino_cohorte_id: '', desde: '', hasta: null },
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Clonar Equipo Docente</h3>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700 mb-1">Materia</label>
            <select id="materia_id" {...register('materia_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
              <option value="">Seleccioná una materia</option>
              {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
            </select>
            {errors.materia_id && <p className="text-red-600 text-xs mt-1">{errors.materia_id.message}</p>}
          </div>

          <div>
            <label htmlFor="carrera_id" className="block text-sm font-medium text-gray-700 mb-1">Carrera</label>
            <select id="carrera_id" {...register('carrera_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
              <option value="">Seleccioná una carrera</option>
              {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            {errors.carrera_id && <p className="text-red-600 text-xs mt-1">{errors.carrera_id.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="origen_cohorte_id" className="block text-sm font-medium text-gray-700 mb-1">Cohorte Origen</label>
              <select id="origen_cohorte_id" {...register('origen_cohorte_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                <option value="">Seleccioná origen</option>
                {cohortes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
              </select>
              {errors.origen_cohorte_id && <p className="text-red-600 text-xs mt-1">{errors.origen_cohorte_id.message}</p>}
            </div>
            <div>
              <label htmlFor="destino_cohorte_id" className="block text-sm font-medium text-gray-700 mb-1">Cohorte Destino</label>
              <select id="destino_cohorte_id" {...register('destino_cohorte_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                <option value="">Seleccioná destino</option>
                {cohortes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
              </select>
              {errors.destino_cohorte_id && <p className="text-red-600 text-xs mt-1">{errors.destino_cohorte_id.message}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="desde" className="block text-sm font-medium text-gray-700 mb-1">Vigencia desde</label>
              <input id="desde" type="date" {...register('desde')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
              {errors.desde && <p className="text-red-600 text-xs mt-1">{errors.desde.message}</p>}
            </div>
            <div>
              <label htmlFor="hasta" className="block text-sm font-medium text-gray-700 mb-1">Vigencia hasta</label>
              <input id="hasta" type="date" {...register('hasta')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onCancel} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={isLoading} className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50">
              {isLoading ? 'Clonando…' : 'Clonar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
