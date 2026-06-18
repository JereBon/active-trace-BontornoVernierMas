import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import type { AvisoCreate, AvisoScope } from '../../types'
import { getUsuarios } from '../../services/equiposService'

const schema = z.object({
  titulo: z.string().min(1, 'El título es requerido').max(300),
  cuerpo: z.string().min(1, 'El cuerpo es requerido'),
  scope: z.enum(['TODOS', 'ROL', 'USUARIO'] as const),
  scope_valor: z.string().nullable().optional(),
  vig_desde: z.string().min(1, 'La fecha de inicio es requerida'),
  vig_hasta: z.string().min(1, 'La fecha de fin es requerida'),
}).refine((d) => new Date(d.vig_hasta) > new Date(d.vig_desde), {
  message: 'La fecha de fin debe ser posterior a la de inicio',
  path: ['vig_hasta'],
})

type FormValues = z.infer<typeof schema>

const SCOPE_LABELS: Record<AvisoScope, string> = {
  TODOS: 'Todos los usuarios',
  ROL: 'Por rol',
  USUARIO: 'Usuario específico',
}

const ROLES_DISPONIBLES = ['PROFESOR', 'TUTOR', 'COORDINADOR', 'NEXO', 'ADMIN', 'FINANZAS']

interface Props {
  onSubmit: (data: AvisoCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

export function AvisoForm({ onSubmit, onCancel, isLoading }: Props) {
  const { data: usuarios = [] } = useQuery({ queryKey: ['usuarios'], queryFn: getUsuarios })

  const {
    register,
    watch,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      titulo: '',
      cuerpo: '',
      scope: 'TODOS',
      scope_valor: null,
      vig_desde: '',
      vig_hasta: '',
    },
  })

  const scope = watch('scope')

  const onValid = (data: FormValues) => {
    onSubmit({
      titulo: data.titulo,
      cuerpo: data.cuerpo,
      scope: data.scope,
      scope_valor: data.scope !== 'TODOS' ? (data.scope_valor ?? null) : null,
      vig_desde: new Date(data.vig_desde).toISOString(),
      vig_hasta: new Date(data.vig_hasta).toISOString(),
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      <div>
        <label htmlFor="titulo" className="block text-sm font-medium text-gray-700 mb-1">Título</label>
        <input id="titulo" {...register('titulo')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" placeholder="Título del aviso" />
        {errors.titulo && <p className="text-red-600 text-xs mt-1">{errors.titulo.message}</p>}
      </div>

      <div>
        <label htmlFor="cuerpo" className="block text-sm font-medium text-gray-700 mb-1">Cuerpo</label>
        <textarea id="cuerpo" {...register('cuerpo')} rows={4} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" placeholder="Contenido del aviso" />
        {errors.cuerpo && <p className="text-red-600 text-xs mt-1">{errors.cuerpo.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="scope" className="block text-sm font-medium text-gray-700 mb-1">Alcance</label>
          <select id="scope" {...register('scope')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
            {(Object.keys(SCOPE_LABELS) as AvisoScope[]).map((s) => (
              <option key={s} value={s}>{SCOPE_LABELS[s]}</option>
            ))}
          </select>
        </div>

        {scope === 'ROL' && (
          <div>
            <label htmlFor="scope_valor" className="block text-sm font-medium text-gray-700 mb-1">Rol destinatario</label>
            <select id="scope_valor" {...register('scope_valor')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
              <option value="">Seleccioná un rol</option>
              {ROLES_DISPONIBLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
        )}

        {scope === 'USUARIO' && (
          <div>
            <label htmlFor="scope_valor_uid" className="block text-sm font-medium text-gray-700 mb-1">Usuario destinatario</label>
            <select id="scope_valor_uid" {...register('scope_valor')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
              <option value="">Seleccioná un usuario</option>
              {usuarios.map((u) => (
                <option key={u.id} value={u.id}>{u.nombre}{u.apellidos ? ' ' + u.apellidos : ''} {u.email ? `(${u.email})` : ''}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="vig_desde" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia desde
          </label>
          <input
            id="vig_desde"
            type="datetime-local"
            {...register('vig_desde')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          {errors.vig_desde && <p className="text-red-600 text-xs mt-1">{errors.vig_desde.message}</p>}
        </div>
        <div>
          <label htmlFor="vig_hasta" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia hasta
          </label>
          <input
            id="vig_hasta"
            type="datetime-local"
            {...register('vig_hasta')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          {errors.vig_hasta && <p className="text-red-600 text-xs mt-1">{errors.vig_hasta.message}</p>}
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
          {isLoading ? 'Publicando…' : 'Publicar'}
        </button>
      </div>
    </form>
  )
}
