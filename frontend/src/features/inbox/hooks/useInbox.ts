import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getRecibidos,
  getEnviados,
  getMensaje,
  enviarMensaje,
  responderMensaje,
} from '@/features/inbox/services/inboxService'
import type {
  MensajeInternoCreate,
  MensajeInternoResponder,
} from '@/features/inbox/types'

const INBOX_KEY = ['inbox']
const ENVIADOS_KEY = ['inbox-enviados']

export function useRecibidos(soloNoLeidos?: boolean) {
  return useQuery({
    queryKey: [...INBOX_KEY, { soloNoLeidos }],
    queryFn: () => getRecibidos(soloNoLeidos),
  })
}

export function useEnviados() {
  return useQuery({ queryKey: ENVIADOS_KEY, queryFn: getEnviados })
}

export function useMensaje(id: string | null) {
  return useQuery({
    queryKey: ['inbox-mensaje', id],
    queryFn: () => getMensaje(id!),
    enabled: Boolean(id),
  })
}

export function useEnviarMensaje() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: MensajeInternoCreate) => enviarMensaje(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: INBOX_KEY })
      qc.invalidateQueries({ queryKey: ENVIADOS_KEY })
    },
  })
}

export function useResponderMensaje() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string
      payload: MensajeInternoResponder
    }) => responderMensaje(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: INBOX_KEY })
      qc.invalidateQueries({ queryKey: ENVIADOS_KEY })
      qc.invalidateQueries({ queryKey: ['inbox-mensaje'] })
    },
  })
}
