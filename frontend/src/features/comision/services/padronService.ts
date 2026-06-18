import { api } from '@/shared/services/api'

export interface EntradaPreview {
  nombre: string
  apellidos: string
  email: string
  comision: string | null
  regional: string | null
}

export interface VersionPadron {
  id: string
  materia_id: string
  cohorte_id: string
  cargado_por: string
  cargado_at: string
  activa: boolean
}

export async function previewPadron(file: File): Promise<EntradaPreview[]> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<EntradaPreview[]>('/v1/padron/preview', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function confirmarPadron(
  materiaId: string,
  cohorteId: string,
  entradas: EntradaPreview[],
): Promise<VersionPadron> {
  const { data } = await api.post<VersionPadron>('/v1/padron/confirmar', {
    materia_id: materiaId,
    cohorte_id: cohorteId,
    entradas,
  })
  return data
}

export async function listarVersionesPadron(materiaId: string): Promise<VersionPadron[]> {
  const { data } = await api.get<VersionPadron[]>(`/v1/padron/materia/${materiaId}`)
  return data
}
