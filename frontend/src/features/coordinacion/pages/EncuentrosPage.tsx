// features/coordinacion/pages/EncuentrosPage.tsx
import { useState } from 'react'
import { TablaEncuentros } from '../components/encuentros/TablaEncuentros'
import { EncuentroForm } from '../components/encuentros/EncuentroForm'
import { useCreateEncuentro } from '../hooks/useEncuentros'
import type { EncuentroCreate } from '../types'

export function EncuentrosPage() {
  const [showForm, setShowForm] = useState(false)
  const createEncuentro = useCreateEncuentro()

  const handleSubmit = (data: EncuentroCreate) => {
    createEncuentro.mutate(data, { onSuccess: () => setShowForm(false) })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Encuentros</h2>
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Nuevo Encuentro
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Nuevo Encuentro</h3>
          <EncuentroForm
            onSubmit={handleSubmit}
            onCancel={() => setShowForm(false)}
            isLoading={createEncuentro.isPending}
          />
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <TablaEncuentros />
      </div>
    </div>
  )
}
