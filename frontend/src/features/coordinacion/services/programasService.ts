import { api } from '@/shared/services/api'

export interface ProgramaMateriaOut {
  id: string
  tenant_id: string
  materia_id: string
  carrera_id: string | null
  cohorte_id: string | null
  titulo: string
  referencia_archivo: string | null
  vigente: boolean
  publicado_en: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface ProgramaMateriaCreate {
  materia_id: string
  carrera_id?: string | null
  cohorte_id?: string | null
  titulo: string
  referencia_archivo?: string | null
  vigente?: boolean
  publicado_en?: string | null
}

export async function getProgramas(): Promise<ProgramaMateriaOut[]> {
  const { data } = await api.get<ProgramaMateriaOut[]>('/v1/programas')
  return data
}

export async function getProgramasByMateria(
  materiaId: string,
): Promise<ProgramaMateriaOut[]> {
  const { data } = await api.get<ProgramaMateriaOut[]>(
    `/v1/programas/materia/${materiaId}`,
  )
  return data
}

export async function createPrograma(
  payload: ProgramaMateriaCreate,
): Promise<ProgramaMateriaOut> {
  const { data } = await api.post<ProgramaMateriaOut>(
    '/v1/programas',
    payload,
  )
  return data
}

export async function deletePrograma(id: string): Promise<void> {
  await api.delete(`/v1/programas/${id}`)
}
