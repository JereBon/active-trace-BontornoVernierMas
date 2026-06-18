import { api } from '@/shared/services/api'

export interface ComunicacionItem {
  id: string
  lote_id: string
  destinatario: string
  asunto: string
  estado: string
  aprobado: boolean
  enviado_at: string | null
  created_at: string
}

export interface LoteStatus {
  lote_id: string
  total: number
  pendientes: number
  enviados: number
  errores: number
  cancelados: number
  mensajes: ComunicacionItem[]
}

export interface LoteResumen {
  lote_id: string
  total: number
  pendientes: number
  enviados: number
  errores: number
  aprobado: boolean
  created_at: string
}

export async function getLotesByMateria(materiaId: string, limit = 20): Promise<LoteResumen[]> {
  const { data } = await api.get<LoteResumen[]>('/v1/comunicaciones/lotes', {
    params: { materia_id: materiaId, limit },
  })
  return data
}

export async function getLoteStatus(loteId: string): Promise<LoteStatus> {
  const { data } = await api.get<LoteStatus>(`/v1/comunicaciones/lotes/${loteId}`)
  return data
}

export async function aprobarLote(loteId: string): Promise<{ lote_id: string; approved: number }> {
  const { data } = await api.patch(`/v1/comunicaciones/lotes/${loteId}/aprobar`)
  return data
}

export async function cancelarLote(loteId: string): Promise<{ lote_id: string; cancelled: number }> {
  const { data } = await api.patch(`/v1/comunicaciones/lotes/${loteId}/cancelar`)
  return data
}
