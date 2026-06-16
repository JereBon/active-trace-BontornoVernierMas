// features/comision/components/FormularioComunicacion.tsx
// React Hook Form + Zod for comunicacion. Preview calls server-side rendering.
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Spinner } from '@/shared/components/Spinner'
import {
  previewComunicacion,
  encolarComunicaciones,
  type EncolarBody,
  type EncolarResponse,
} from '../services/comunicacionesService'
import type { PreviewComunicacion } from '../types'

const schema = z.object({
  asunto: z.string().min(1, 'El asunto es requerido'),
  cuerpo: z.string().min(1, 'El cuerpo es requerido'),
})

type FormValues = z.infer<typeof schema>

interface Props {
  materiaId: string
  /** Recipients derived from atrasados list */
  destinatarios: Array<{ email: string; variables?: Record<string, string> }>
  onEnviado: (response: EncolarResponse) => void
}

export function FormularioComunicacion({ materiaId, destinatarios, onEnviado }: Props) {
  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const previewMut = useMutation<PreviewComunicacion, Error, FormValues>({
    mutationFn: (values) =>
      previewComunicacion({ asunto: values.asunto, cuerpo: values.cuerpo }),
  })

  const encolarMut = useMutation<EncolarResponse, Error, EncolarBody>({
    mutationFn: encolarComunicaciones,
    onSuccess: onEnviado,
  })

  function handlePreview() {
    const values = getValues()
    if (!values.asunto || !values.cuerpo) return
    previewMut.mutate(values)
  }

  function onSubmit(values: FormValues) {
    encolarMut.mutate({
      materia_id: materiaId || undefined,
      asunto: values.asunto,
      cuerpo: values.cuerpo,
      destinatarios,
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="asunto" className="block text-sm font-medium text-gray-700">
          Asunto
        </label>
        <input
          id="asunto"
          type="text"
          {...register('asunto')}
          placeholder="Asunto del mensaje"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none"
        />
        {errors.asunto && (
          <p role="alert" className="mt-1 text-xs text-red-600">
            {errors.asunto.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="cuerpo" className="block text-sm font-medium text-gray-700">
          Cuerpo{' '}
          <span className="text-xs text-gray-400">
            (usá {'{{nombre}}'}, {'{{materia}}'} para variables)
          </span>
        </label>
        <textarea
          id="cuerpo"
          rows={6}
          {...register('cuerpo')}
          placeholder="Estimado {{nombre}}, te recordamos que..."
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none"
        />
        {errors.cuerpo && (
          <p role="alert" className="mt-1 text-xs text-red-600">
            {errors.cuerpo.message}
          </p>
        )}
      </div>

      {previewMut.error && (
        <p role="alert" className="text-sm text-red-600">
          Error en preview: {previewMut.error.message}
        </p>
      )}
      {encolarMut.error && (
        <p role="alert" className="text-sm text-red-600">
          Error al enviar: {encolarMut.error.message}
        </p>
      )}

      <p className="text-xs text-gray-500">
        {destinatarios.length} destinatario{destinatarios.length !== 1 ? 's' : ''}
      </p>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={handlePreview}
          disabled={previewMut.isPending}
          className="flex items-center gap-2 rounded-md border border-blue-600 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 disabled:opacity-50"
        >
          {previewMut.isPending && <Spinner />}
          Vista previa
        </button>

        <button
          type="submit"
          disabled={encolarMut.isPending || destinatarios.length === 0}
          className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {encolarMut.isPending && <Spinner />}
          {encolarMut.isPending ? 'Enviando…' : 'Enviar'}
        </button>
      </div>

      {/* Inline preview result */}
      {previewMut.data && (
        <div className="rounded-md bg-gray-50 p-4 text-sm">
          <p className="font-semibold text-gray-700">Preview del asunto:</p>
          <p className="mt-1 text-gray-800">{previewMut.data.asunto}</p>
          <p className="mt-3 font-semibold text-gray-700">Preview del cuerpo:</p>
          <p className="mt-1 whitespace-pre-wrap text-gray-800">{previewMut.data.cuerpo}</p>
        </div>
      )}
    </form>
  )
}
