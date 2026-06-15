// features/coordinacion/pages/EquiposPage.tsx
import { useState } from 'react'
import { TablaEquipos } from '../components/equipos/TablaEquipos'
import { EquipoForm } from '../components/equipos/EquipoForm'
import { useCreateEquipo, useUpdateEquipo } from '../hooks/useEquipos'
import type { EquipoDocente, EquipoDocenteCreate } from '../types'
import { useUsuarios } from '@/features/admin/hooks/useUsuarios'
import { PageHelp } from '@/shared/components/PageHelp'
import { helpContent } from '@/shared/utils/helpContent'

export function EquiposPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingEquipo, setEditingEquipo] = useState<EquipoDocente | null>(null)
  const [responsableId, setResponsableId] = useState('')
  const createEquipo = useCreateEquipo()
  const updateEquipo = useUpdateEquipo()
  const { data: usuarios = [] } = useUsuarios()

  const handleSubmit = (data: EquipoDocenteCreate) => {
    if (editingEquipo) {
      const { usuario_id: _uid, ...updatePayload } = data
      updateEquipo.mutate(
        { id: editingEquipo.id, payload: updatePayload },
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
        <div className="flex items-center gap-3">
          <select
            value={responsableId}
            onChange={(e) => setResponsableId(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm bg-white"
          >
            <option value="">— Todos los responsables —</option>
            {usuarios.map((u) => (
              <option key={u.id} value={u.id}>{u.nombre} {u.apellidos}</option>
            ))}
          </select>
          <PageHelp>{helpContent.equipos}</PageHelp>
          <button
            onClick={() => { setEditingEquipo(null); setShowForm(true) }}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Nueva Asignación
          </button>
        </div>
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
            isEditing={!!editingEquipo}
          />
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <TablaEquipos onEdit={handleEdit} responsableId={responsableId || undefined} />
      </div>
    </div>
  )
}
