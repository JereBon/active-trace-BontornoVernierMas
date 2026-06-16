// features/comision/components/PreviewComunicacionPanel.tsx
// Displays server-rendered preview of a communication.
import type { PreviewComunicacion } from '../types'

interface Props {
  preview: PreviewComunicacion
}

export function PreviewComunicacionPanel({ preview }: Props) {
  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 space-y-3">
      <h4 className="text-sm font-semibold text-blue-800">Vista previa del mensaje</h4>
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-blue-600">Asunto</p>
        <p className="mt-1 text-sm text-gray-800">{preview.asunto}</p>
      </div>
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-blue-600">Cuerpo</p>
        <p className="mt-1 whitespace-pre-wrap text-sm text-gray-800">{preview.cuerpo}</p>
      </div>
    </div>
  )
}
