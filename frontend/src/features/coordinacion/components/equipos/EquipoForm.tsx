// features/coordinacion/components/equipos/EquipoForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { ROLES_ASIGNACION } from '../../types'
import type { Asignacion, AsignacionCreate } from '../../types'
import { getUsuarios } from '../../services/equiposService'
import { getCarreras, getCohortes, getMaterias } from '@/features/admin/services/estructuraService'

const schema = z.object({
  usuario_id: z.string().uuid('Seleccioná un docente'),
  rol: z.enum(ROLES_ASIGNACION, { required_error: 'El rol es requerido' }),
  desde: z.string().min(1, 'La fecha de inicio es requerida'),
  hasta: z.string().nullable().optional(),
  materia_id: z.string().uuid().nullable().optional().or(z.literal('')),
  carrera_id: z.string().uuid().nullable().optional().or(z.literal('')),
  cohorte_id: z.string().uuid().nullable().optional().or(z.literal('')),
})

type FormValues = z.infer<typeof schema>

interface Props {
  defaultValues?: Partial<Asignacion>
  onSubmit: (data: AsignacionCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

export function EquipoForm({ defaultValues, onSubmit, onCancel, isLoading }: Props) {
  const { data: usuarios = [] } = useQuery({ queryKey: ['usuarios'], queryFn: getUsuarios })
  const { data: materias = [] } = useQuery({ queryKey: ['materias'], queryFn: getMaterias })
  const { data: carreras = [] } = useQuery({ queryKey: ['carreras'], queryFn: getCarreras })
  const { data: cohortes = [] } = useQuery({ queryKey: ['cohortes-all'], queryFn: () => getCohortes() })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      usuario_id: defaultValues?.usuario_id ?? '',
      rol: (defaultValues?.rol as typeof ROLES_ASIGNACION[number]) ?? 'PROFESOR',
      desde: defaultValues?.desde ?? '',
      hasta: defaultValues?.hasta ?? null,
      materia_id: defaultValues?.materia_id ?? '',
      carrera_id: defaultValues?.carrera_id ?? '',
      cohorte_id: defaultValues?.cohorte_id ?? '',
    },
  })

  const onValid = (data: FormValues) => {
    onSubmit({
      usuario_id: data.usuario_id,
      rol: data.rol,
      desde: data.desde,
      hasta: data.hasta ?? null,
      materia_id: data.materia_id || null,
      carrera_id: data.carrera_id || null,
      cohorte_id: data.cohorte_id || null,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      <div>
        <label htmlFor="usuario_id" className="block text-sm font-medium text-gray-700 mb-1">
          Docente
        </label>
        <select
          id="usuario_id"
          {...register('usuario_id')}
          disabled={!!defaultValues?.id}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Seleccioná un docente</option>
          {usuarios.map((u) => (
            <option key={u.id} value={u.id}>
              {u.nombre}{u.apellidos ? ' ' + u.apellidos : ''} {u.email ? `(${u.email})` : ''}
            </option>
          ))}
        </select>
        {errors.usuario_id && <p className="text-red-600 text-xs mt-1">{errors.usuario_id.message}</p>}
      </div>

      <div>
        <label htmlFor="rol" className="block text-sm font-medium text-gray-700 mb-1">
          Rol
        </label>
        <select
          id="rol"
          {...register('rol')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
        >
          {ROLES_ASIGNACION.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
        {errors.rol && <p className="text-red-600 text-xs mt-1">{errors.rol.message}</p>}
      </div>

      <div>
        <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700 mb-1">
          Materia
        </label>
        <select
          id="materia_id"
          {...register('materia_id')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
        >
          <option value="">Sin materia</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>{m.nombre} ({m.codigo})</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="carrera_id" className="block text-sm font-medium text-gray-700 mb-1">
            Carrera
          </label>
          <select
            id="carrera_id"
            {...register('carrera_id')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          >
            <option value="">Sin carrera</option>
            {carreras.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre} ({c.codigo})</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="cohorte_id" className="block text-sm font-medium text-gray-700 mb-1">
            Cohorte
          </label>
          <select
            id="cohorte_id"
            {...register('cohorte_id')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          >
            <option value="">Sin cohorte</option>
            {cohortes.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre} ({c.anio})</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="desde" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia desde
          </label>
          <input
            id="desde"
            type="date"
            {...register('desde')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          {errors.desde && <p className="text-red-600 text-xs mt-1">{errors.desde.message}</p>}
        </div>
        <div>
          <label htmlFor="hasta" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia hasta (opcional)
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
          {isLoading ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}
