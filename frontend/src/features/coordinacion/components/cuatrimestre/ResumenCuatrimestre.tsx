// features/coordinacion/components/cuatrimestre/ResumenCuatrimestre.tsx
import { useCohortes } from '@/features/admin/hooks/useEstructura'
import type { ClonarConfig } from './PasoEquiposForm'

interface Props {
  materias: string[]
  cohortes: string[]
  clonarConfig: Record<string, ClonarConfig>
  onConfirm: () => void
  onBack: () => void
  isConfirming?: boolean
  errorMsg?: string | null
}

export function ResumenCuatrimestre({
  materias,
  cohortes,
  clonarConfig,
  onConfirm,
  onBack,
  isConfirming,
  errorMsg,
}: Props) {
  const { data: todasCohortes = [] } = useCohortes()

  const cohorteLabel = (id: string) => {
    const c = todasCohortes.find((co) => co.id === id)
    return c ? `${c.anio}${c.plan ? ` (${c.plan})` : ''}` : id
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-800">Paso 3: Confirmar Configuración</h3>

      <div className="bg-gray-50 rounded-lg p-4 space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Materias seleccionadas</h4>
          {materias.length === 0 ? (
            <p className="text-sm text-gray-400">Ninguna</p>
          ) : (
            <ul className="space-y-1">
              {materias.map((m) => (
                <li key={m} className="text-sm text-gray-700">• {m}</li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Clonado de equipos por cohorte</h4>
          {cohortes.length === 0 ? (
            <p className="text-sm text-gray-400">Ninguna</p>
          ) : (
            <ul className="space-y-2">
              {cohortes.map((cohorteDestinoId) => {
                const cfg = clonarConfig[cohorteDestinoId]
                return (
                  <li key={cohorteDestinoId} className="text-sm text-gray-700">
                    <span className="font-medium">{cohorteLabel(cfg?.origen_cohorte_id ?? '?')}</span>
                    {' → '}
                    <span className="font-medium">{cohorteLabel(cohorteDestinoId)}</span>
                    {cfg?.desde && (
                      <span className="text-gray-500"> (inicio: {cfg.desde})</span>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>

      {errorMsg && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
          {errorMsg}
        </p>
      )}

      <div className="flex justify-between">
        <button
          onClick={onBack}
          disabled={isConfirming}
          className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
        >
          Anterior
        </button>
        <button
          onClick={onConfirm}
          disabled={isConfirming}
          className="px-4 py-2 text-sm text-white bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
        >
          {isConfirming ? 'Confirmando...' : 'Confirmar Cuatrimestre'}
        </button>
      </div>
    </div>
  )
}
