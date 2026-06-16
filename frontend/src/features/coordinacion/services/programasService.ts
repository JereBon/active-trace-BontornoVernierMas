// features/coordinacion/services/programasService.ts
import { api } from '@/shared/services/api'

export interface ProgramaCreate {
  materia_id: string
  carrera_id?: string | null
  cohorte_id?: string | null
  titulo: string
  referencia_archivo?: string | null
  vigente: boolean
}

export interface ProgramaOut extends ProgramaCreate {
  id: string
  tenant_id: string
  publicado_en: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export async function getProgramas(): Promise<ProgramaOut[]> {
  const { data } = await api.get<ProgramaOut[]>('/v1/programas')
  return data
}

export async function createPrograma(payload: ProgramaCreate): Promise<ProgramaOut> {
  const { data } = await api.post<ProgramaOut>('/v1/programas', payload)
  return data
}

export async function deletePrograma(id: string): Promise<void> {
  await api.delete(`/v1/programas/${id}`)
}
