// features/coordinacion/hooks/useTareas.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createComentario,
  createTarea,
  getComentarios,
  getTareas,
  updateTarea,
} from '../services/tareasService'
import type { ComentarioTareaCreate, TareaCreate, TareaUpdate } from '../types'

const TAREAS_KEY = ['tareas']

export function useTareas() {
  return useQuery({ queryKey: TAREAS_KEY, queryFn: getTareas })
}

export function useCreateTarea() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: TareaCreate) => createTarea(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: TAREAS_KEY }),
  })
}

export function useUpdateTarea() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: TareaUpdate }) =>
      updateTarea(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: TAREAS_KEY }),
  })
}

export function useComentarios(tareaId: string) {
  return useQuery({
    queryKey: ['tareas', tareaId, 'comentarios'],
    queryFn: () => getComentarios(tareaId),
    enabled: Boolean(tareaId),
  })
}

export function useCreateComentario(tareaId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ComentarioTareaCreate) => createComentario(tareaId, payload),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ['tareas', tareaId, 'comentarios'] }),
  })
}
