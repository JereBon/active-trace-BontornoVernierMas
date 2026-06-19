import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Spinner } from '@/shared/components/Spinner'
import { api } from '@/shared/services/api'
import { useAuth } from '@/features/auth/hooks/useAuth'
import type { MensajeInterno } from '@/features/inbox/types'

interface UserOption {
  id: string
  nombre: string
  apellidos: string
  email: string
}

interface MessageDetailProps {
  mensaje: MensajeInterno
  onReply: (cuerpo: string) => Promise<void>
}

export function MessageDetail({ mensaje, onReply }: MessageDetailProps) {
  const { user } = useAuth()
  const [replyText, setReplyText] = useState('')
  const [sending, setSending] = useState(false)

  const { data: users = [] } = useQuery<UserOption[]>({
    queryKey: ['usuarios-search'],
    queryFn: async () => {
      const { data } = await api.get<UserOption[]>('/v1/usuarios/search')
      return data
    },
  })

  const userMap = useMemo(() => {
    const map = new Map<string, UserOption>()
    for (const u of users) {
      map.set(u.id, u)
    }
    return map
  }, [users])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!replyText.trim()) return

    setSending(true)
    try {
      await onReply(replyText.trim())
      setReplyText('')
    } finally {
      setSending(false)
    }
  }

  const allMessages = [mensaje, ...(mensaje.respuestas ?? [])]

  function senderLabel(msg: MensajeInterno): string {
    const u = userMap.get(msg.remitente_id)
    if (msg.remitente_id === user?.id) return 'Vos'
    if (u) return `${u.nombre} ${u.apellidos}`
    return msg.remitente_id.slice(0, 8)
  }

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString('es-AR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {mensaje.asunto}
          </h3>
          {mensaje.hilo_id && (
            <p className="text-xs text-gray-400 mt-1">Hilo de mensajes</p>
          )}
        </div>

        <div className="flex flex-col gap-3">
          {allMessages.map((msg) => {
            const isMine = msg.remitente_id === user?.id
            return (
              <div
                key={msg.id}
                className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                    isMine
                      ? 'rounded-br-md bg-brand-600 text-white'
                      : 'rounded-bl-md bg-gray-100 text-gray-800'
                  }`}
                >
                  {!isMine && (
                    <p className="mb-0.5 text-xs font-medium text-gray-500">
                      {senderLabel(msg)}
                    </p>
                  )}
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">
                    {msg.cuerpo}
                  </p>
                  <p
                    className={`mt-1 text-right text-[10px] ${
                      isMine ? 'text-brand-200' : 'text-gray-400'
                    }`}
                  >
                    {formatDate(msg.created_at)}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} noValidate className="space-y-3">
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder="Escribí tu respuesta…"
            rows={3}
            disabled={sending}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!replyText.trim() || sending}
              className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {sending ? <Spinner size="sm" /> : null}
              {sending ? 'Enviando…' : 'Responder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
