// features/coordinacion/pages/AvisosPage.tsx
import { useState } from 'react'
import { TablaAvisos } from '../components/avisos/TablaAvisos'
import { AvisoForm } from '../components/avisos/AvisoForm'
import { useCreateAviso } from '../hooks/useAvisos'
import type { AvisoCreate } from '../types'

export function AvisosPage() {
  const [showForm, setShowForm] = useState(false)
  const createAviso = useCreateAviso()

  const handleSubmit = (data: AvisoCreate) => {
    createAviso.mutate(data, { onSuccess: () => setShowForm(false) })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Avisos</h2>
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Nuevo Aviso
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Publicar Aviso</h3>
          <AvisoForm
            onSubmit={handleSubmit}
            onCancel={() => setShowForm(false)}
            isLoading={createAviso.isPending}
          />
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <TablaAvisos />
      </div>
    </div>
  )
}
