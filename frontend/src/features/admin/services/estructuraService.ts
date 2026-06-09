// features/admin/services/estructuraService.ts
import { api } from '@/shared/services/api'
import type {
  Carrera,
  CarreraCreate,
  CarreraUpdate,
  Cohorte,
  CohorteCreate,
  CohorteUpdate,
  Materia,
  MateriaCreate,
  MateriaUpdate,
} from '../types'

// ─── Carreras ─────────────────────────────────────────────────────────────────

export async function getCarreras(): Promise<Carrera[]> {
  const { data } = await api.get<Carrera[]>('/v1/carreras')
  return data
}

export async function createCarrera(payload: CarreraCreate): Promise<Carrera> {
  const { data } = await api.post<Carrera>('/v1/carreras', payload)
  return data
}

export async function updateCarrera(id: string, payload: CarreraUpdate): Promise<Carrera> {
  const { data } = await api.patch<Carrera>(`/v1/carreras/${id}`, payload)
  return data
}

export async function deleteCarrera(id: string): Promise<void> {
  await api.delete(`/v1/carreras/${id}`)
}

// ─── Cohortes ─────────────────────────────────────────────────────────────────

export async function getCohortes(carreraId?: string): Promise<Cohorte[]> {
  const { data } = await api.get<Cohorte[]>('/v1/cohortes', {
    params: carreraId ? { carrera_id: carreraId } : undefined,
  })
  return data
}

export async function createCohorte(payload: CohorteCreate): Promise<Cohorte> {
  const { data } = await api.post<Cohorte>('/v1/cohortes', payload)
  return data
}

export async function updateCohorte(id: string, payload: CohorteUpdate): Promise<Cohorte> {
  const { data } = await api.patch<Cohorte>(`/v1/cohortes/${id}`, payload)
  return data
}

// ─── Materias ─────────────────────────────────────────────────────────────────

export async function getMaterias(): Promise<Materia[]> {
  const { data } = await api.get<Materia[]>('/v1/materias')
  return data
}

export async function createMateria(payload: MateriaCreate): Promise<Materia> {
  const { data } = await api.post<Materia>('/v1/materias', payload)
  return data
}

export async function updateMateria(id: string, payload: MateriaUpdate): Promise<Materia> {
  const { data } = await api.patch<Materia>(`/v1/materias/${id}`, payload)
  return data
}
