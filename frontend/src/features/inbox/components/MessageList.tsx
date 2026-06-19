import type { MensajeInterno } from '@/features/inbox/types'

interface MessageListProps {
  mensajes: MensajeInterno[]
  selectedId: string | null
  onSelect: (m: MensajeInterno) => void
  emptyLabel: string
}

export function MessageList({
  mensajes,
  selectedId,
  onSelect,
  emptyLabel,
}: MessageListProps) {
  if (mensajes.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-400">{emptyLabel}</p>
    )
  }

  return (
    <div className="divide-y divide-gray-100">
      {mensajes.map((m) => {
        const isActive = m.id === selectedId
        return (
          <button
            key={m.id}
            onClick={() => onSelect(m)}
            className={`w-full px-4 py-3 text-left transition hover:bg-gray-50 ${
              isActive ? 'bg-blue-50' : ''
            }`}
          >
            <div className="flex items-center justify-between">
              <span
                className={`text-sm ${
                  !m.leido
                    ? 'font-semibold text-gray-900'
                    : 'font-medium text-gray-700'
                }`}
              >
                {m.asunto}
              </span>
              {!m.leido && (
                <span className="h-2 w-2 rounded-full bg-blue-600" />
              )}
            </div>
            <p className="mt-0.5 truncate text-xs text-gray-500">
              {m.cuerpo}
            </p>
            <p className="mt-1 text-xs text-gray-400">
              {new Date(m.created_at).toLocaleDateString('es-AR', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </button>
        )
      })}
    </div>
  )
}
