// features/comision/components/TrackingLotePanel.tsx
// Shows counters for the batch with polling via useLoteStatus.
import { Spinner } from '@/shared/components/Spinner'
import { useLoteStatus } from '../hooks/useLoteStatus'

interface Props {
  loteId: string
}

interface CounterProps {
  label: string
  value: number
  colorClass: string
}

function Counter({ label, value, colorClass }: CounterProps) {
  return (
    <div className="flex flex-col items-center rounded-lg border border-gray-200 bg-white p-3 shadow-sm min-w-[80px]">
      <span className={`text-2xl font-bold ${colorClass}`}>{value}</span>
      <span className="mt-1 text-xs text-gray-500">{label}</span>
    </div>
  )
}

export function TrackingLotePanel({ loteId }: Props) {
  const { data, isLoading, error } = useLoteStatus(loteId)

  if (isLoading) return (
    <div className="flex items-center gap-2 text-sm text-gray-500">
      <Spinner size="sm" />
      Cargando estado del lote…
    </div>
  )

  if (error) return (
    <p className="text-sm text-red-600">Error al obtener el estado: {error.message}</p>
  )

  if (!data) return null

  const isTerminal = data.pendientes === 0

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h4 className="text-sm font-semibold text-gray-700">
          Estado del lote
        </h4>
        {!isTerminal && (
          <span className="flex items-center gap-1 text-xs text-blue-600">
            <Spinner size="sm" />
            Actualizando…
          </span>
        )}
        {isTerminal && (
          <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
            Completado
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-3" data-testid="lote-counters">
        <Counter label="Pendientes" value={data.pendientes} colorClass="text-yellow-600" />
        <Counter label="Enviados" value={data.enviados} colorClass="text-green-600" />
        <Counter label="Errores" value={data.errores} colorClass="text-red-600" />
        <Counter label="Cancelados" value={data.cancelados} colorClass="text-gray-500" />
      </div>

      <p className="text-xs text-gray-400">Lote ID: {data.lote_id}</p>
    </div>
  )
}
