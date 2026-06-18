import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAtrasados } from '../hooks/useAtrasados'
import { FormularioComunicacion } from '../components/FormularioComunicacion'
import { TrackingLotePanel } from '../components/TrackingLotePanel'
import { Spinner } from '@/shared/components/Spinner'
import {
  getLotesMateria,
  aprobarLote,
  cancelarLote,
  encolarDesdePadron,
  type EncolarResponse,
  type LoteResumen,
} from '../services/comunicacionesService'

export function ComunicacionPage() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const [loteId, setLoteId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const atrasados = useAtrasados(materiaId ?? '')

  const { data: lotes = [], refetch: refetchLotes } = useQuery({
    queryKey: ['lotes-materia', materiaId],
    queryFn: () => getLotesMateria(materiaId!),
    enabled: !!materiaId,
    refetchInterval: 10_000,
  })

  const aprobarMut = useMutation({
    mutationFn: (id: string) => aprobarLote(id),
    onSuccess: () => refetchLotes(),
  })

  const cancelarMut = useMutation({
    mutationFn: (id: string) => cancelarLote(id),
    onSuccess: () => refetchLotes(),
  })

  if (!materiaId) return null

  const atrasadosData = atrasados.data ?? []
  const entradaIds = atrasadosData.map((a) => a.entrada_padron_id)

  function handleEnviado(response: EncolarResponse) {
    setLoteId(response.lote_id)
    void refetchLotes()
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
          {entradaIds.length === 0 ? (
            <p className="text-sm text-gray-500">
              No hay alumnos atrasados para esta materia.
            </p>
          ) : (
            <FormularioComunicacion
              materiaId={materiaId}
              entradaPadronIds={entradaIds}
              destinatariosCount={entradaIds.length}
              onEnviado={handleEnviado}
            />
          )}
        </>
      )}

      {loteId && (
        <div>
          <hr className="border-gray-200 mb-6" />
          <TrackingLotePanel loteId={loteId} />
        </div>
      )}

      {/* Historial de lotes */}
      {lotes.length > 0 && (
        <div>
          <hr className="border-gray-200 mb-4" />
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Historial de envíos</h3>
          <ul className="space-y-2">
            {lotes.map((lote) => (
              <LoteRow
                key={lote.lote_id}
                lote={lote}
                onAprobar={() => aprobarMut.mutate(lote.lote_id)}
                onCancelar={() => cancelarMut.mutate(lote.lote_id)}
                onVer={() => setLoteId(lote.lote_id)}
                loadingAprobar={aprobarMut.isPending && aprobarMut.variables === lote.lote_id}
                loadingCancelar={cancelarMut.isPending && cancelarMut.variables === lote.lote_id}
              />
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

interface LoteRowProps {
  lote: LoteResumen
  onAprobar: () => void
  onCancelar: () => void
  onVer: () => void
  loadingAprobar: boolean
  loadingCancelar: boolean
}

function LoteRow({ lote, onAprobar, onCancelar, onVer, loadingAprobar, loadingCancelar }: LoteRowProps) {
  const fecha = new Date(lote.created_at).toLocaleString('es-AR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

  const todoEnviado = lote.enviados === lote.total && lote.total > 0
  const hayPendientes = lote.pendientes > 0
  const necesitaAprobacion = hayPendientes && !lote.aprobado

  return (
    <li className="rounded-md border border-gray-200 bg-white p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-0.5">
          <p className="text-xs text-gray-400">{fecha}</p>
          <p className="text-gray-700">
            {lote.total} destinatario{lote.total !== 1 ? 's' : ''} —{' '}
            <span className="text-green-600">{lote.enviados} enviados</span>
            {lote.pendientes > 0 && (
              <span className="ml-1 text-yellow-600">{lote.pendientes} pendientes</span>
            )}
            {lote.errores > 0 && (
              <span className="ml-1 text-red-600">{lote.errores} errores</span>
            )}
          </p>
          {necesitaAprobacion && (
            <p className="text-xs text-orange-600 font-medium">
              ⚠ Requiere aprobación antes de enviarse
            </p>
          )}
        </div>

        <div className="flex shrink-0 gap-1">
          <button
            onClick={onVer}
            className="rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50"
          >
            Ver detalle
          </button>
          {necesitaAprobacion && (
            <button
              onClick={onAprobar}
              disabled={loadingAprobar}
              className="rounded bg-green-600 px-2 py-1 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {loadingAprobar ? '…' : 'Aprobar'}
            </button>
          )}
          {hayPendientes && (
            <button
              onClick={onCancelar}
              disabled={loadingCancelar}
              className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-50"
            >
              {loadingCancelar ? '…' : 'Cancelar'}
            </button>
          )}
        </div>
      </div>
    </li>
  )
}
