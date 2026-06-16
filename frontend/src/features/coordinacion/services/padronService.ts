// features/coordinacion/services/padronService.ts
import { api } from '@/shared/services/api'

export interface EntradaPreview {
  nombre: string
  apellidos: string
  email: string
  comision?: string | null
  regional?: string | null
}

export interface ConfirmarPadronPayload {
  materia_id: string
  cohorte_id: string
  entradas: EntradaPreview[]
}

export async function previewPadron(file: File): Promise<EntradaPreview[]> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<EntradaPreview[]>('/v1/padron/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function confirmarPadron(payload: ConfirmarPadronPayload): Promise<void> {
  await api.post('/v1/padron/confirmar', payload)
}

export async function vaciarPadron(materiaId: string): Promise<void> {
  await api.delete(`/v1/padron/materia/${materiaId}`)
}
