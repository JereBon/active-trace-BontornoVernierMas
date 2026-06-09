// features/comision/pages/ComunicacionPage.tsx
// Communication form + preview panel + tracking.
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAtrasados } from '../hooks/useAtrasados'
import { FormularioComunicacion } from '../components/FormularioComunicacion'
import { TrackingLotePanel } from '../components/TrackingLotePanel'
import { Spinner } from '@/shared/components/Spinner'
import type { EncolarResponse } from '../services/comunicacionesService'

export function ComunicacionPage() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const [loteId, setLoteId] = useState<string | null>(null)

  const atrasados = useAtrasados(materiaId ?? '')

  if (!materiaId) return null

  // Build recipients from atrasados: use their entrada_padron_id as email placeholder
  // In a full implementation this would use actual student emails from the padron.
  // The backend encrypts destinatarios, so we pass the emails available from the API.
  // atrasados don't expose emails directly — the padron has them.
  // We construct a minimal destinatarios list using the display data.
  const destinatarios = (atrasados.data ?? []).map((a) => ({
    email: `alumno-${a.entrada_padron_id}@placeholder.invalid`,
    variables: {
      nombre: a.nombre,
      apellidos: a.apellidos,
      comision: a.comision ?? '',
    },
  }))

  function handleEnviado(response: EncolarResponse) {
    setLoteId(response.lote_id)
  }

  return (
    <div className="space-y-8 max-w-2xl">
      <h2 className="text-lg font-semibold text-gray-900">Comunicaciones a atrasados</h2>

      {atrasados.isLoading && (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Spinner size="sm" />
          Cargando lista de atrasados…
        </div>
      )}

      {!atrasados.isLoading && (
        <>
          {destinatarios.length === 0 ? (
            <p className="text-sm text-gray-500">
              No hay alumnos atrasados para esta materia. No se pueden enviar comunicaciones.
            </p>
          ) : (
            <FormularioComunicacion
              materiaId={materiaId}
              destinatarios={destinatarios}
              onEnviado={handleEnviado}
            />
          )}

          {loteId && (
            <div>
              <hr className="border-gray-200 mb-6" />
              <TrackingLotePanel loteId={loteId} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
