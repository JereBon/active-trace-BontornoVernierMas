// features/coordinacion/pages/EquiposPage.tsx
import { useState } from 'react'
import { TablaEquipos } from '../components/equipos/TablaEquipos'
import { EquipoForm } from '../components/equipos/EquipoForm'
import { useCreateEquipo, useUpdateEquipo } from '../hooks/useEquipos'
import type { EquipoDocente, EquipoDocenteCreate } from '../types'

export function EquiposPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingEquipo, setEditingEquipo] = useState<EquipoDocente | null>(null)
  const createEquipo = useCreateEquipo()
  const updateEquipo = useUpdateEquipo()

  const handleSubmit = (data: EquipoDocenteCreate) => {
    if (editingEquipo) {
      updateEquipo.mutate(
        { id: editingEquipo.id, payload: data },
        { onSuccess: () => { setShowForm(false); setEditingEquipo(null) } },
      )
    } else {
      createEquipo.mutate(data, {
        onSuccess: () => setShowForm(false),
      })
    }
  }

  const handleEdit = (equipo: EquipoDocente) => {
    setEditingEquipo(equipo)
    setShowForm(true)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Asignaciones Docentes</h2>
        <button
          onClick={() => { setEditingEquipo(null); setShowForm(true) }}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Nueva Asignación
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {editingEquipo ? 'Editar Asignación' : 'Nueva Asignación'}
          </h3>
          <EquipoForm
            defaultValues={editingEquipo ?? undefined}
            onSubmit={handleSubmit}
            onCancel={() => { setShowForm(false); setEditingEquipo(null) }}
            isLoading={createEquipo.isPending || updateEquipo.isPending}
          />
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <TablaEquipos onEdit={handleEdit} />
      </div>
    </div>
  )
}
