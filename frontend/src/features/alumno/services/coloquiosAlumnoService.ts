import { api } from '@/shared/services/api'

export interface ColoquioDisponible {
  id: string
  materia_id: string
  cohorte_id: string
  tipo: string
  instancia: string
  dias_disponibles: number
  cupos_disponibles: number
  estado: string
}

export interface ReservaOut {
  id: string
  evaluacion_id: string
  alumno_id: string
  fecha_hora: string
  estado: string
  created_at: string
  updated_at: string
}

export interface ReservaCreate {
  fecha_hora: string
}

export async function getColoquiosDisponibles(): Promise<ColoquioDisponible[]> {
  const { data } = await api.get<ColoquioDisponible[]>('/v1/coloquios/disponibles')
  return data
}

export async function getMisReservas(): Promise<ReservaOut[]> {
  const { data } = await api.get<ReservaOut[]>('/v1/coloquios/mis-reservas')
  return data
}

export async function crearReserva(evaluacionId: string, fecha_hora: string): Promise<ReservaOut> {
  const { data } = await api.post<ReservaOut>(`/v1/coloquios/${evaluacionId}/reservas`, { fecha_hora })
  return data
}

export async function cancelarReserva(evaluacionId: string, reservaId: string): Promise<ReservaOut> {
  const { data } = await api.post<ReservaOut>(`/v1/coloquios/${evaluacionId}/reservas/${reservaId}/cancelar`)
  return data
}
