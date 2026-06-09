// features/coordinacion/pages/TareasPage.tsx
import { useState } from 'react'
import { TablaTareas } from '../components/tareas/TablaTareas'
import { HiloComentarios } from '../components/tareas/HiloComentarios'
import { TareaEstadoSelector } from '../components/tareas/TareaEstadoSelector'
import { useCreateTarea, useUpdateTarea } from '../hooks/useTareas'
import type { Tarea, TareaCreate, TareaEstado } from '../types'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const tareaSchema = z.object({
  titulo: z.string().min(1, 'El título es requerido'),
  descripcion: z.string().nullable().optional(),
  prioridad: z.enum(['baja', 'media', 'alta']),
})

type TareaFormValues = z.infer<typeof tareaSchema>

export function TareasPage() {
  const [showForm, setShowForm] = useState(false)
  const [selectedTarea, setSelectedTarea] = useState<Tarea | null>(null)
  const createTarea = useCreateTarea()
  const updateTarea = useUpdateTarea()

  const { register, handleSubmit, reset, formState: { errors } } = useForm<TareaFormValues>({
    resolver: zodResolver(tareaSchema),
    defaultValues: { titulo: '', descripcion: null, prioridad: 'media' },
  })

  const onSubmit = (data: TareaFormValues) => {
    const payload: TareaCreate = {
      titulo: data.titulo,
      descripcion: data.descripcion ?? null,
      prioridad: data.prioridad,
    }
    createTarea.mutate(payload, {
      onSuccess: () => { setShowForm(false); reset() },
    })
  }

  const handleEstadoChange = (nuevoEstado: TareaEstado) => {
    if (!selectedTarea) return
    updateTarea.mutate(
      { id: selectedTarea.id, payload: { estado: nuevoEstado } },
      { onSuccess: () => setSelectedTarea((prev) => prev ? { ...prev, estado: nuevoEstado } : prev) },
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Tareas</h2>
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Nueva Tarea
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Nueva Tarea</h3>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label htmlFor="titulo-tarea" className="block text-sm font-medium text-gray-700 mb-1">
                Título
              </label>
              <input
                id="titulo-tarea"
                {...register('titulo')}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              />
              {errors.titulo && <p className="text-red-600 text-xs mt-1">{errors.titulo.message}</p>}
            </div>
            <div>
              <label htmlFor="prioridad-tarea" className="block text-sm font-medium text-gray-700 mb-1">
                Prioridad
              </label>
              <select
                id="prioridad-tarea"
                {...register('prioridad')}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option value="baja">Baja</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
              </select>
            </div>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => { setShowForm(false); reset() }}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={createTarea.isPending}
                className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Crear
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="flex gap-6">
        <div className="flex-1 bg-white border border-gray-200 rounded-lg p-4">
          <TablaTareas onSelect={setSelectedTarea} />
        </div>

        {selectedTarea && (
          <div className="w-80 bg-white border border-gray-200 rounded-lg p-4 space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900">{selectedTarea.titulo}</h3>
              {selectedTarea.descripcion && (
                <p className="text-sm text-gray-600 mt-1">{selectedTarea.descripcion}</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Estado</label>
              <TareaEstadoSelector
                tareaId={selectedTarea.id}
                estadoActual={selectedTarea.estado}
                onChange={handleEstadoChange}
                disabled={updateTarea.isPending}
              />
            </div>
            <HiloComentarios tareaId={selectedTarea.id} />
          </div>
        )}
      </div>
    </div>
  )
}
