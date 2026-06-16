// features/coordinacion/hooks/useTareas.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  cambiarEstadoTarea,
  createComentario,
  createTarea,
  delegarTarea,
  getComentarios,
  getTareas,
} from '../services/tareasService'
import type { ComentarioTareaCreate, TareaCreate, TareaEstado } from '../types'

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

export function useCambiarEstadoTarea() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: TareaEstado }) =>
      cambiarEstadoTarea(id, estado),
    onSuccess: () => qc.invalidateQueries({ queryKey: TAREAS_KEY }),
  })
}

export function useDelegarTarea() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, nuevo_asignado_id }: { id: string; nuevo_asignado_id: string }) =>
      delegarTarea(id, nuevo_asignado_id),
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
