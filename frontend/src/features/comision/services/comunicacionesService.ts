// features/comision/services/comunicacionesService.ts
// All HTTP calls via the centralised Axios instance (JWT injected automatically).

import { api } from '@/shared/services/api'
import type { LoteStatus, PreviewComunicacion } from '../types'

export interface PreviewBody {
  asunto: string
  cuerpo: string
  variables?: Record<string, string>
}

export interface DestinatarioItem {
  email: string
  variables?: Record<string, string>
}

export interface EncolarBody {
  materia_id?: string
  asunto: string
  cuerpo: string
  destinatarios: DestinatarioItem[]
}

export interface EncolarResponse {
  lote_id: string
  count: number
  requiere_aprobacion: boolean
}

/** POST /v1/comunicaciones/preview — server-side rendering, no DB write */
export async function previewComunicacion(body: PreviewBody): Promise<PreviewComunicacion> {
  const { data } = await api.post<PreviewComunicacion>('/v1/comunicaciones/preview', body)
  return data
}

/** POST /v1/comunicaciones/encolar — enqueue a batch */
export async function encolarComunicaciones(body: EncolarBody): Promise<EncolarResponse> {
  const { data } = await api.post<EncolarResponse>('/v1/comunicaciones/encolar', body)
  return data
}

/** GET /v1/comunicaciones/lotes/{loteId} — poll lote status */
export async function getLoteStatus(loteId: string): Promise<LoteStatus> {
  const { data } = await api.get<LoteStatus>(`/v1/comunicaciones/lotes/${loteId}`)
  return data
}
