// features/coordinacion/pages/AvisosPage.tsx
import { useState } from 'react'
import { TablaAvisos } from '../components/avisos/TablaAvisos'
import { AvisoForm } from '../components/avisos/AvisoForm'
import { useCreateAviso, useUpdateAviso } from '../hooks/useAvisos'
import type { Aviso, AvisoCreate } from '../types'
import { PageHelp } from '@/shared/components/PageHelp'
import { helpContent } from '@/shared/utils/helpContent'

export function AvisosPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingAviso, setEditingAviso] = useState<Aviso | null>(null)
  const createAviso = useCreateAviso()
  const updateAviso = useUpdateAviso()

  const handleClose = () => { setShowForm(false); setEditingAviso(null) }

  const handleSubmit = (data: AvisoCreate) => {
    if (editingAviso) {
      updateAviso.mutate(
        { id: editingAviso.id, payload: data },
        { onSuccess: handleClose },
      )
    } else {
      createAviso.mutate(data, { onSuccess: handleClose })
    }
  }

  const handleEdit = (aviso: Aviso) => {
    setEditingAviso(aviso)
    setShowForm(true)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Avisos</h2>
        <div className="flex items-center gap-2">
          <PageHelp>{helpContent.avisos}</PageHelp>
          <button
            onClick={() => { setEditingAviso(null); setShowForm(true) }}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Nuevo Aviso
          </button>
        </div>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {editingAviso ? 'Editar Aviso' : 'Publicar Aviso'}
          </h3>
          <AvisoForm
            defaultValues={editingAviso ?? undefined}
            onSubmit={handleSubmit}
            onCancel={handleClose}
            isLoading={createAviso.isPending || updateAviso.isPending}
          />
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <TablaAvisos onEdit={handleEdit} />
      </div>
    </div>
  )
}
