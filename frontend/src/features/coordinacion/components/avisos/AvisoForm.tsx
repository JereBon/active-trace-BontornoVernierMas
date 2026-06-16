// features/coordinacion/components/avisos/AvisoForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { Aviso, AvisoCreate } from '../../types'
import { useUsuarios } from '@/features/admin/hooks/useUsuarios'

const SCOPES = ['TODOS', 'ROL', 'USUARIO'] as const
const ROLES_SISTEMA = ['ALUMNO', 'TUTOR', 'PROFESOR', 'COORDINADOR', 'NEXO', 'ADMIN', 'FINANZAS'] as const

const schema = z.object({
  titulo: z.string().min(1, 'El título es requerido'),
  cuerpo: z.string().min(1, 'El cuerpo es requerido'),
  scope: z.enum(SCOPES).default('TODOS'),
  scope_valor: z.string().nullable().optional(),
  vig_desde: z.string().min(1, 'La fecha de inicio es requerida'),
  vig_hasta: z.string().min(1, 'La fecha de fin es requerida'),
})

type FormValues = z.infer<typeof schema>

interface Props {
  defaultValues?: Aviso
  onSubmit: (data: AvisoCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

const toLocalInput = (iso: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function AvisoForm({ defaultValues, onSubmit, onCancel, isLoading }: Props) {
  const { data: usuarios = [] } = useUsuarios()
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      titulo: defaultValues?.titulo ?? '',
      cuerpo: defaultValues?.cuerpo ?? '',
      scope: (defaultValues?.scope as typeof SCOPES[number]) ?? 'TODOS',
      scope_valor: defaultValues?.scope_valor ?? null,
      vig_desde: defaultValues ? toLocalInput(defaultValues.vig_desde) : '',
      vig_hasta: defaultValues ? toLocalInput(defaultValues.vig_hasta) : '',
    },
  })

  const scope = watch('scope')

  const toUTCISO = (localStr: string) => new Date(localStr).toISOString()

  const onValid = (data: FormValues) => {
    onSubmit({
      titulo: data.titulo,
      cuerpo: data.cuerpo,
      scope: data.scope,
      scope_valor: data.scope_valor ?? null,
      vig_desde: toUTCISO(data.vig_desde),
      vig_hasta: toUTCISO(data.vig_hasta),
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      <div>
        <label htmlFor="titulo" className="block text-sm font-medium text-gray-700 mb-1">
          Título <span className="text-red-500">*</span>
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
          Cuerpo <span className="text-red-500">*</span>
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
            Audiencia
          </label>
          <select
            id="scope"
            {...register('scope')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          >
            <option value="TODOS">Todos</option>
            <option value="ROL">Por Rol</option>
            <option value="USUARIO">Usuario específico</option>
          </select>
        </div>

        {scope !== 'TODOS' && (
          <div>
            <label htmlFor="scope_valor" className="block text-sm font-medium text-gray-700 mb-1">
              {scope === 'ROL' ? 'Rol' : 'UUID de Usuario'}
            </label>
            {scope === 'ROL' ? (
              <select
                id="scope_valor"
                {...register('scope_valor')}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
              >
                <option value="">— Seleccioná un rol —</option>
                {ROLES_SISTEMA.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            ) : (
              <select
                id="scope_valor"
                {...register('scope_valor')}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
              >
                <option value="">— Seleccioná un usuario —</option>
                {usuarios.map((u) => (
                  <option key={u.id} value={u.id}>{u.nombre} {u.apellidos}</option>
                ))}
              </select>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="vig_desde" className="block text-sm font-medium text-gray-700 mb-1">
            Vigente desde <span className="text-red-500">*</span>
          </label>
          <input
            id="vig_desde"
            type="datetime-local"
            {...register('vig_desde')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          {errors.vig_desde && (
            <p className="text-red-600 text-xs mt-1">{errors.vig_desde.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="vig_hasta" className="block text-sm font-medium text-gray-700 mb-1">
            Vigente hasta <span className="text-red-500">*</span>
          </label>
          <input
            id="vig_hasta"
            type="datetime-local"
            {...register('vig_hasta')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          {errors.vig_hasta && (
            <p className="text-red-600 text-xs mt-1">{errors.vig_hasta.message}</p>
          )}
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
          {defaultValues ? 'Guardar cambios' : 'Publicar'}
        </button>
      </div>
    </form>
  )
}
