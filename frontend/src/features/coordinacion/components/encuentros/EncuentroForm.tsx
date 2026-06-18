// features/coordinacion/components/encuentros/EncuentroForm.tsx
// Aligned with backend SlotCreate schema
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { getMaterias } from '@/features/admin/services/estructuraService'
import { DIAS_SEMANA } from './constantes'
import type { SlotCreate, DiaSemana } from '../../types'

const schema = z.discriminatedUnion('modo', [
  z.object({
    modo: z.literal('recurrente'),
    materia_id: z.string().uuid('Seleccioná una materia'),
    titulo: z.string().min(1, 'El título es requerido'),
    dia_semana: z.enum(DIAS_SEMANA as [string, ...string[]]),
    hora: z.string().regex(/^\d{2}:\d{2}$/, 'Formato HH:MM'),
    fecha_inicio: z.string().min(1, 'La fecha de inicio es requerida'),
    cant_semanas: z.coerce.number().int().min(1, 'Al menos 1 semana'),
    meet_url: z.string().url('URL inválida').optional().or(z.literal('')),
  }),
  z.object({
    modo: z.literal('unico'),
    materia_id: z.string().uuid('Seleccioná una materia'),
    titulo: z.string().min(1, 'El título es requerido'),
    fecha_unica: z.string().min(1, 'La fecha es requerida'),
    hora: z.string().regex(/^\d{2}:\d{2}$/, 'Formato HH:MM'),
    meet_url: z.string().url('URL inválida').optional().or(z.literal('')),
  }),
])

type FormValues = z.infer<typeof schema>

interface Props {
  onSubmit: (data: SlotCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

export function EncuentroForm({ onSubmit, onCancel, isLoading }: Props) {
  const [modo, setModo] = useState<'recurrente' | 'unico'>('recurrente')
  const { data: materias = [] } = useQuery({ queryKey: ['materias'], queryFn: getMaterias })

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { modo: 'recurrente', materia_id: '', titulo: '', hora: '', meet_url: '' },
  })

  const switchModo = (m: 'recurrente' | 'unico') => {
    setModo(m)
    reset({ modo: m, materia_id: '', titulo: '', hora: '', meet_url: '' })
  }

  const onValid = (data: FormValues) => {
    const base = {
      asignacion_id: '',
      materia_id: data.materia_id,
      titulo: data.titulo,
      hora: data.hora,
      meet_url: data.meet_url || null,
    }
    if (data.modo === 'recurrente') {
      onSubmit({ ...base, dia_semana: data.dia_semana, fecha_inicio: data.fecha_inicio, cant_semanas: data.cant_semanas, fecha_unica: null } as SlotCreate)
    } else {
      onSubmit({ ...base, dia_semana: 'Lunes', fecha_inicio: data.fecha_unica, cant_semanas: 0, fecha_unica: data.fecha_unica } as SlotCreate)
    }
  }

  return (
    <form onSubmit={handleSubmit(onValid)} className="space-y-4">
      {/* Modo selector */}
      <div className="flex gap-2 mb-2">
        <button type="button" onClick={() => switchModo('recurrente')} className={`px-3 py-1 text-sm rounded ${modo === 'recurrente' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}>Recurrente</button>
        <button type="button" onClick={() => switchModo('unico')} className={`px-3 py-1 text-sm rounded ${modo === 'unico' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}>Único</button>
      </div>

      <div>
        <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700 mb-1">Materia</label>
        <select id="materia_id" {...register('materia_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
          <option value="">Seleccioná una materia</option>
          {materias.map((m) => <option key={m.id} value={m.id}>{m.nombre} ({m.codigo})</option>)}
        </select>
        {errors.materia_id && <p className="text-red-600 text-xs mt-1">{errors.materia_id.message}</p>}
      </div>

      <div>
        <label htmlFor="titulo" className="block text-sm font-medium text-gray-700 mb-1">Título</label>
        <input id="titulo" {...register('titulo')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" placeholder="Ej: Clase 1" />
        {errors.titulo && <p className="text-red-600 text-xs mt-1">{errors.titulo.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="hora" className="block text-sm font-medium text-gray-700 mb-1">Horario (HH:MM)</label>
          <input id="hora" {...register('hora')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" placeholder="18:00" />
          {errors.hora && <p className="text-red-600 text-xs mt-1">{errors.hora.message}</p>}
        </div>
        <div>
          <label htmlFor="meet_url" className="block text-sm font-medium text-gray-700 mb-1">Link videoconferencia</label>
          <input id="meet_url" {...register('meet_url')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" placeholder="https://meet.google.com/..." />
        </div>
      </div>

      {modo === 'recurrente' ? (
        <>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label htmlFor="dia_semana" className="block text-sm font-medium text-gray-700 mb-1">Día de la semana</label>
              <select id="dia_semana" {...register('dia_semana')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                {DIAS_SEMANA.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
              {errors.dia_semana && <p className="text-red-600 text-xs mt-1">{errors.dia_semana.message}</p>}
            </div>
            <div>
              <label htmlFor="fecha_inicio" className="block text-sm font-medium text-gray-700 mb-1">Fecha inicio</label>
              <input id="fecha_inicio" type="date" {...register('fecha_inicio')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
              {errors.fecha_inicio && <p className="text-red-600 text-xs mt-1">{errors.fecha_inicio.message}</p>}
            </div>
            <div>
              <label htmlFor="cant_semanas" className="block text-sm font-medium text-gray-700 mb-1">N° semanas</label>
              <input id="cant_semanas" type="number" min={1} {...register('cant_semanas')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
              {errors.cant_semanas && <p className="text-red-600 text-xs mt-1">{errors.cant_semanas.message}</p>}
            </div>
          </div>
        </>
      ) : (
        <div>
          <label htmlFor="fecha_unica" className="block text-sm font-medium text-gray-700 mb-1">Fecha del encuentro</label>
          <input id="fecha_unica" type="date" {...register('fecha_unica')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          {errors.fecha_unica && <p className="text-red-600 text-xs mt-1">{errors.fecha_unica.message}</p>}
        </div>
      )}

      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50">Cancelar</button>
        <button type="submit" disabled={isLoading} className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50">
          {isLoading ? 'Creando…' : 'Crear Encuentro'}
        </button>
      </div>
    </form>
  )
}
