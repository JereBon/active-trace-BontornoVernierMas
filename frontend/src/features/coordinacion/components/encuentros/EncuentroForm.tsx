// features/coordinacion/components/encuentros/EncuentroForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { EncuentroCreate } from '../../types'

const DIAS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo'] as const

const schema = z.object({
  asignacion_id: z.string().uuid('Debe ser un UUID válido'),
  materia_id: z.string().uuid('Debe ser un UUID válido'),
  titulo: z.string().min(1, 'El título es requerido'),
  hora: z.string().regex(/^\d{2}:\d{2}$/, 'Formato HH:MM'),
  dia_semana: z.enum(DIAS),
  fecha_inicio: z.string().min(1, 'La fecha es requerida'),
  cant_semanas: z.coerce.number().int().min(0),
  meet_url: z.string().url().optional().or(z.literal('')),
})

type FormValues = z.infer<typeof schema>

interface Props {
  onSubmit: (data: EncuentroCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

export function EncuentroForm({ onSubmit, onCancel, isLoading }: Props) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { hora: '09:00', dia_semana: 'Lunes', cant_semanas: 1 },
  })

  const onValid = (data: FormValues) => {
    onSubmit({
      asignacion_id: data.asignacion_id,
      materia_id: data.materia_id,
      titulo: data.titulo,
      hora: data.hora,
      dia_semana: data.dia_semana,
      fecha_inicio: data.fecha_inicio,
      cant_semanas: data.cant_semanas,
      meet_url: data.meet_url || null,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Asignación ID <span className="text-red-500">*</span>
          </label>
          <input {...register('asignacion_id')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono"
            placeholder="UUID de la asignación" />
          {errors.asignacion_id && <p className="text-red-600 text-xs mt-1">{errors.asignacion_id.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Materia ID <span className="text-red-500">*</span>
          </label>
          <input {...register('materia_id')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono"
            placeholder="UUID de la materia" />
          {errors.materia_id && <p className="text-red-600 text-xs mt-1">{errors.materia_id.message}</p>}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Título <span className="text-red-500">*</span></label>
        <input {...register('titulo')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="Ej: Clase teórica semanal" />
        {errors.titulo && <p className="text-red-600 text-xs mt-1">{errors.titulo.message}</p>}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Día <span className="text-red-500">*</span></label>
          <select {...register('dia_semana')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
            {DIAS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Hora <span className="text-red-500">*</span></label>
          <input type="time" {...register('hora')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          {errors.hora && <p className="text-red-600 text-xs mt-1">{errors.hora.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Semanas (0=única)</label>
          <input type="number" min="0" {...register('cant_semanas')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Fecha inicio <span className="text-red-500">*</span></label>
        <input type="date" {...register('fecha_inicio')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        {errors.fecha_inicio && <p className="text-red-600 text-xs mt-1">{errors.fecha_inicio.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Link Meet</label>
        <input {...register('meet_url')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="https://meet.google.com/..." />
        {errors.meet_url && <p className="text-red-600 text-xs mt-1">{errors.meet_url.message}</p>}
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onCancel}
          className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50">
          Cancelar
        </button>
        <button type="submit" disabled={isLoading}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50">
          Guardar
        </button>
      </div>
    </form>
  )
}
