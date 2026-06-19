import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useRecibidos, useEnviados, useMensaje, useEnviarMensaje, useResponderMensaje } from '@/features/inbox/hooks/useInbox'
import { MessageList } from '@/features/inbox/components/MessageList'
import { MessageDetail } from '@/features/inbox/components/MessageDetail'
import { ComposeMessageModal } from '@/features/inbox/components/ComposeMessageModal'
import { Spinner } from '@/shared/components/Spinner'
import type { MensajeInterno, MensajeInternoCreate } from '@/features/inbox/types'

type Tab = 'recibidos' | 'enviados'

export function InboxPage() {
  const [tab, setTab] = useState<Tab>('recibidos')
  const [selectedMsg, setSelectedMsg] = useState<MensajeInterno | null>(null)
  const [showCompose, setShowCompose] = useState(false)
  const [soloNoLeidos, setSoloNoLeidos] = useState(false)

  const { data: recibidos = [], isLoading: loadingRecibidos } = useRecibidos(soloNoLeidos || undefined)
  const { data: enviados = [], isLoading: loadingEnviados } = useEnviados()
  const { data: mensajeDetail, isLoading: loadingDetail } = useMensaje(selectedMsg?.id ?? null)

  const sendMsg = useEnviarMensaje()
  const replyMsg = useResponderMensaje()

  const activeList = tab === 'recibidos' ? recibidos : enviados
  const isLoading = tab === 'recibidos' ? loadingRecibidos : loadingEnviados

  const handleSelect = (m: MensajeInterno) => {
    setSelectedMsg(m)
  }

  const handleSend = async (data: MensajeInternoCreate) => {
    await sendMsg.mutateAsync(data)
    setShowCompose(false)
  }

  const handleReply = async (cuerpo: string) => {
    if (!selectedMsg) return
    await replyMsg.mutateAsync({ id: selectedMsg.id, payload: { cuerpo } })
  }

  const displayedMessage = mensajeDetail ?? selectedMsg
  const queryClient = useQueryClient()

  // Re-fetch inbox list when a message is opened (leido status may have changed)
  useEffect(() => {
    if (mensajeDetail) {
      queryClient.invalidateQueries({ queryKey: ['inbox'] })
    }
  }, [mensajeDetail, queryClient])

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mensajes</h1>
          <p className="mt-1 text-sm text-gray-500">
            Bandeja de entrada y mensajería interna.
          </p>
        </div>
        <button
          onClick={() => setShowCompose(true)}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Nuevo mensaje
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden rounded-xl border border-gray-200 bg-white">
        <div className="flex w-80 flex-col border-r border-gray-200">
          <div className="border-b border-gray-200">
            <div className="flex">
              <button
                onClick={() => { setTab('recibidos'); setSelectedMsg(null) }}
                className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                  tab === 'recibidos'
                    ? 'border-b-2 border-brand-600 text-brand-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Recibidos
              </button>
              <button
                onClick={() => { setTab('enviados'); setSelectedMsg(null) }}
                className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                  tab === 'enviados'
                    ? 'border-b-2 border-brand-600 text-brand-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Enviados
              </button>
            </div>
            {tab === 'recibidos' && (
              <label className="flex items-center gap-2 px-4 pb-3 pt-2">
                <input
                  type="checkbox"
                  checked={soloNoLeidos}
                  onChange={(e) => setSoloNoLeidos(e.target.checked)}
                  className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                />
                <span className="text-xs text-gray-500">Solo no leídos</span>
              </label>
            )}
          </div>

          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Spinner />
              </div>
            ) : (
              <MessageList
                mensajes={activeList}
                selectedId={selectedMsg?.id ?? null}
                onSelect={handleSelect}
                emptyLabel={
                  tab === 'recibidos' ? 'No hay mensajes recibidos.' : 'No hay mensajes enviados.'
                }
              />
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loadingDetail ? (
            <div className="flex items-center justify-center py-12">
              <Spinner />
            </div>
          ) : displayedMessage ? (
            <MessageDetail
              key={displayedMessage.id}
              mensaje={displayedMessage}
              onReply={handleReply}
            />
          ) : (
            <div className="flex items-center justify-center py-12">
              <p className="text-sm text-gray-400">
                Seleccioná un mensaje para leerlo
              </p>
            </div>
          )}
        </div>
      </div>

      {showCompose && (
        <ComposeMessageModal
          onSend={handleSend}
          onClose={() => setShowCompose(false)}
        />
      )}
    </div>
  )
}
