import { api } from '@/shared/services/api'
import type {
  MensajeInterno,
  MensajeInternoCreate,
  MensajeInternoResponder,
} from '@/features/inbox/types'

export async function getRecibidos(
  soloNoLeidos?: boolean,
): Promise<MensajeInterno[]> {
  const params = soloNoLeidos ? { solo_no_leidos: true } : undefined
  const { data } = await api.get<MensajeInterno[]>('/v1/inbox', { params })
  return data
}

export async function getEnviados(): Promise<MensajeInterno[]> {
  const { data } = await api.get<MensajeInterno[]>('/v1/inbox/enviados')
  return data
}

export async function getMensaje(id: string): Promise<MensajeInterno> {
  const { data } = await api.get<MensajeInterno>(`/v1/inbox/${id}`)
  return data
}

export async function enviarMensaje(
  payload: MensajeInternoCreate,
): Promise<MensajeInterno> {
  const { data } = await api.post<MensajeInterno>('/v1/inbox', payload)
  return data
}

export async function responderMensaje(
  id: string,
  payload: MensajeInternoResponder,
): Promise<MensajeInterno> {
  const { data } = await api.post<MensajeInterno>(
    `/v1/inbox/${id}/responder`,
    payload,
  )
  return data
}
