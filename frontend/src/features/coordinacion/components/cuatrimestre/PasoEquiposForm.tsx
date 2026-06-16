// features/coordinacion/components/cuatrimestre/PasoEquiposForm.tsx
import { useState } from 'react'
import { useCohortes } from '@/features/admin/hooks/useEstructura'

export interface ClonarConfig {
  origen_cohorte_id: string
  desde: string // YYYY-MM-DD
}

interface Props {
  cohortes: string[] // cohorte destino IDs (seleccionadas en paso 1)
  onNext: (config: Record<string, ClonarConfig>) => void
  onBack: () => void
}

export function PasoEquiposForm({ cohortes, onNext, onBack }: Props) {
  const { data: todasCohortes = [] } = useCohortes()
  const [config, setConfig] = useState<Record<string, ClonarConfig>>({})

  const setField = (
    cohorteDestinoId: string,
    field: keyof ClonarConfig,
    value: string,
  ) => {
    setConfig((prev) => ({
      ...prev,
      [cohorteDestinoId]: {
        origen_cohorte_id: prev[cohorteDestinoId]?.origen_cohorte_id ?? '',
        desde: prev[cohorteDestinoId]?.desde ?? '',
        [field]: value,
      },
    }))
  }

  const cohorteLabel = (id: string) => {
    const c = todasCohortes.find((co) => co.id === id)
    return c ? `${c.anio}${c.plan ? ` (${c.plan})` : ''}` : id
  }

  const isComplete = cohortes.every(
    (id) => config[id]?.origen_cohorte_id && config[id]?.desde,
  )

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-800">Paso 2: Configurar Clonado de Equipos</h3>

      {cohortes.length === 0 ? (
        <p className="text-gray-400 text-sm">No hay cohortes seleccionadas.</p>
      ) : (
        <div className="space-y-4">
          {cohortes.map((cohorteDestinoId) => {
            const origenOptions = todasCohortes.filter((c) => c.id !== cohorteDestinoId)
            return (
              <div key={cohorteDestinoId} className="bg-gray-50 rounded-lg p-4 space-y-3">
                <p className="text-sm font-semibold text-gray-700">
                  Cohorte destino: {cohorteLabel(cohorteDestinoId)}
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Clonar desde:
                    </label>
                    <select
                      value={config[cohorteDestinoId]?.origen_cohorte_id ?? ''}
                      onChange={(e) => setField(cohorteDestinoId, 'origen_cohorte_id', e.target.value)}
                      className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm bg-white"
                    >
                      <option value="">— Seleccioná cohorte origen —</option>
                      {origenOptions.map((c) => (
                        <option key={c.id} value={c.id}>
                          {cohorteLabel(c.id)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Fecha inicio:
                    </label>
                    <input
                      type="date"
                      value={config[cohorteDestinoId]?.desde ?? ''}
                      onChange={(e) => setField(cohorteDestinoId, 'desde', e.target.value)}
                      className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
                    />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
        >
          Anterior
        </button>
        <button
          onClick={() => onNext(config)}
          disabled={!isComplete}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Siguiente
        </button>
      </div>
    </div>
  )
}
