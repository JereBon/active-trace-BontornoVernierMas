import { useState } from 'react'
import { TablaEquipos } from '../components/equipos/TablaEquipos'
import { EquipoForm } from '../components/equipos/EquipoForm'
import { AsignacionMasivaModal } from '../components/equipos/AsignacionMasivaModal'
import { ClonarEquipoModal } from '../components/equipos/ClonarEquipoModal'
import { VigenciaMasivaModal } from '../components/equipos/VigenciaMasivaModal'
import { useCreateEquipo, useUpdateEquipo, useAsignacionMasiva, useClonarEquipo, useVigenciaMasiva } from '../hooks/useEquipos'
import type { Asignacion, AsignacionCreate } from '../types'

export function EquiposPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingAsignacion, setEditingAsignacion] = useState<Asignacion | null>(null)
  const [showMasiva, setShowMasiva] = useState(false)
  const [showClonar, setShowClonar] = useState(false)
  const [showVigencia, setShowVigencia] = useState(false)

  const createEquipo = useCreateEquipo()
  const updateEquipo = useUpdateEquipo()
  const masiva = useAsignacionMasiva()
  const clonar = useClonarEquipo()
  const vigencia = useVigenciaMasiva()

  const handleSubmit = (data: AsignacionCreate) => {
    if (editingAsignacion) {
      const { usuario_id: _uid, ...updatePayload } = data
      updateEquipo.mutate(
        { id: editingAsignacion.id, payload: updatePayload },
        { onSuccess: () => { setShowForm(false); setEditingAsignacion(null) } },
      )
    } else {
      createEquipo.mutate(data, {
        onSuccess: () => setShowForm(false),
      })
    }
  }

  const handleEdit = (asignacion: Asignacion) => {
    setEditingAsignacion(asignacion)
    setShowForm(true)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Equipos Docentes</h2>
        <div className="flex gap-2">
          <button onClick={() => setShowVigencia(true)} className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
            Modificar Vigencia
          </button>
          <button onClick={() => setShowClonar(true)} className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
            Clonar Equipo
          </button>
          <button onClick={() => { setShowMasiva(true); setShowForm(false) }} className="px-3 py-1.5 text-sm border border-blue-300 text-blue-700 rounded hover:bg-blue-50">
            Asignación Masiva
          </button>
          <button
            onClick={() => { setEditingAsignacion(null); setShowForm(true); setShowMasiva(false); setShowClonar(false); setShowVigencia(false) }}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Nueva Asignación
          </button>
        </div>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {editingAsignacion ? 'Editar Asignación' : 'Nueva Asignación'}
          </h3>
          <EquipoForm
            defaultValues={editingAsignacion ?? undefined}
            onSubmit={handleSubmit}
            onCancel={() => { setShowForm(false); setEditingAsignacion(null) }}
            isLoading={createEquipo.isPending || updateEquipo.isPending}
          />
        </div>
      )}

      {showMasiva && (
        <AsignacionMasivaModal
          onSubmit={(data) => masiva.mutate(data, { onSuccess: () => setShowMasiva(false) })}
          onCancel={() => setShowMasiva(false)}
          isLoading={masiva.isPending}
        />
      )}

      {showClonar && (
        <ClonarEquipoModal
          onSubmit={(data) => clonar.mutate(data, { onSuccess: () => setShowClonar(false) })}
          onCancel={() => setShowClonar(false)}
          isLoading={clonar.isPending}
        />
      )}

      {showVigencia && (
        <VigenciaMasivaModal
          onSubmit={(data) => vigencia.mutate(data, { onSuccess: () => setShowVigencia(false) })}
          onCancel={() => setShowVigencia(false)}
          isLoading={vigencia.isPending}
        />
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <TablaEquipos onEdit={handleEdit} />
      </div>
    </div>
  )
}
