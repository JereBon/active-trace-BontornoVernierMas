import { api } from '@/shared/services/api'

export type TipoEvaluacion = 'PARCIAL' | 'TP' | 'COLOQUIO' | 'RECUPERATORIO'

export interface FechaAcademicaOut {
  id: string
  tenant_id: string
  materia_id: string
  cohorte_id: string
  tipo: TipoEvaluacion
  numero: number
  periodo: string
  fecha: string
  titulo: string
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface FechaAcademicaCreate {
  materia_id: string
  cohorte_id: string
  tipo: TipoEvaluacion
  numero: number
  periodo: string
  fecha: string
  titulo: string
}

export async function getFechas(
  materiaId?: string,
): Promise<FechaAcademicaOut[]> {
  const params = materiaId ? { materia_id: materiaId } : undefined
  const { data } = await api.get<FechaAcademicaOut[]>(
    '/v1/fechas-academicas',
    { params },
  )
  return data
}

export async function createFecha(
  payload: FechaAcademicaCreate,
): Promise<FechaAcademicaOut> {
  const { data } = await api.post<FechaAcademicaOut>(
    '/v1/fechas-academicas',
    payload,
  )
  return data
}

export async function deleteFecha(id: string): Promise<void> {
  await api.delete(`/v1/fechas-academicas/${id}`)
}
