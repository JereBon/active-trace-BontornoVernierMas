// features/coordinacion/services/tareasService.ts
import { api } from '@/shared/services/api'
import type { ComentarioTarea, ComentarioTareaCreate, Tarea, TareaCreate, TareaEstado } from '../types'

export async function getTareas(): Promise<Tarea[]> {
  const { data } = await api.get<Tarea[]>('/v1/tareas/todas')
  return data
}

export async function getMisTareas(): Promise<Tarea[]> {
  const { data } = await api.get<Tarea[]>('/v1/tareas')
  return data
}

export async function createTarea(payload: TareaCreate): Promise<Tarea> {
  const { data } = await api.post<Tarea>('/v1/tareas', payload)
  return data
}

export async function cambiarEstadoTarea(id: string, estado: TareaEstado): Promise<Tarea> {
  const { data } = await api.patch<Tarea>(`/v1/tareas/${id}/estado`, { estado })
  return data
}

export async function delegarTarea(id: string, nuevo_asignado_id: string): Promise<Tarea> {
  const { data } = await api.post<Tarea>(`/v1/tareas/${id}/delegar`, { nuevo_asignado_id })
  return data
}

export async function getComentarios(tareaId: string): Promise<ComentarioTarea[]> {
  const { data } = await api.get<ComentarioTarea[]>(`/v1/tareas/${tareaId}/comentarios`)
  return data
}

export async function createComentario(
  tareaId: string,
  payload: ComentarioTareaCreate,
): Promise<ComentarioTarea> {
  const { data } = await api.post<ComentarioTarea>(`/v1/tareas/${tareaId}/comentarios`, payload)
  return data
}
