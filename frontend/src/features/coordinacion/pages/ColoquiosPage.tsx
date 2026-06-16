// features/coordinacion/pages/ColoquiosPage.tsx
import { useState } from 'react'
import { TablaColoquios } from '../components/coloquios/TablaColoquios'
import { ColoquioForm } from '../components/coloquios/ColoquioForm'
import { useCreateColoquio } from '../hooks/useColoquios'
import type { ColoquioCreate } from '../types'

export function ColoquiosPage() {
  const [showForm, setShowForm] = useState(false)
  const createColoquio = useCreateColoquio()

  const handleSubmit = (data: ColoquioCreate) => {
    createColoquio.mutate(data, { onSuccess: () => setShowForm(false) })
  }

  return (
    <div className="space-y-4">
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
