// features/coordinacion/pages/ColoquiosPage.tsx
import { useState } from 'react'
import { TablaColoquios } from '../components/coloquios/TablaColoquios'
import { ColoquioForm } from '../components/coloquios/ColoquioForm'
import { useCreateColoquio, useMetricasColoquios } from '../hooks/useColoquios'
import type { EvaluacionCreate } from '../types'

export function ColoquiosPage() {
  const [showForm, setShowForm] = useState(false)
  const createColoquio = useCreateColoquio()
  const { data: metricas } = useMetricasColoquios()

  const handleSubmit = (data: EvaluacionCreate) => {
    createColoquio.mutate(data, { onSuccess: () => setShowForm(false) })
  }

  return (
    <div className="space-y-4">
      {/* KPIs */}
      {metricas && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-gray-800">{metricas.total_convocatorias}</p>
            <p className="text-xs text-gray-500">Convocatorias activas</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-gray-800">{metricas.total_cupos_libres}</p>
            <p className="text-xs text-gray-500">Cupos libres</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-gray-800">{metricas.total_reservas_activas}</p>
            <p className="text-xs text-gray-500">Reservas activas</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-gray-800">{metricas.total_resultados}</p>
            <p className="text-xs text-gray-500">Notas registradas</p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Coloquios</h2>
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Nueva Convocatoria
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Nueva Convocatoria</h3>
          <ColoquioForm
            onSubmit={handleSubmit}
            onCancel={() => setShowForm(false)}
            isLoading={createColoquio.isPending}
          />
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <TablaColoquios />
      </div>
    </div>
  )
}
