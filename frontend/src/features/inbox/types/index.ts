export interface MensajeInterno {
  id: string
  tenant_id: string
  remitente_id: string
  destinatario_id: string
  asunto: string
  cuerpo: string
  leido: boolean
  hilo_id: string | null
  created_at: string
  updated_at: string
  respuestas?: MensajeInterno[]
}

export interface MensajeInternoCreate {
  destinatario_id: string
  asunto: string
  cuerpo: string
}

export interface MensajeInternoResponder {
  cuerpo: string
}
