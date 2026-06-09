// features/coordinacion/components/cuatrimestre/PasoEquiposForm.tsx
import { useState } from 'react'
import { useEquipos } from '../../hooks/useEquipos'

interface Props {
  materias: string[]
  onNext: (asignaciones: Record<string, string>) => void
  onBack: () => void
}

export function PasoEquiposForm({ materias, onNext, onBack }: Props) {
  const { data: equipos = [] } = useEquipos()
  const [asignaciones, setAsignaciones] = useState<Record<string, string>>({})

  const handleChange = (materiaId: string, equipoId: string) => {
    setAsignaciones((prev) => ({ ...prev, [materiaId]: equipoId }))
  }

  const handleNext = () => {
    onNext(asignaciones)
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-800">Paso 2: Asignación de Equipos</h3>

      {materias.length === 0 ? (
        <p className="text-gray-400 text-sm">No hay materias seleccionadas.</p>
      ) : (
        <div className="space-y-3">
          {materias.map((materiaId) => (
            <div key={materiaId} className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-700 w-32 truncate">
                {materiaId}
              </span>
              <select
                value={asignaciones[materiaId] ?? ''}
                onChange={(e) => handleChange(materiaId, e.target.value)}
                className="border border-gray-300 rounded px-2 py-1 text-sm flex-1"
              >
                <option value="">Sin equipo</option>
                {equipos.map((eq) => (
                  <option key={eq.id} value={eq.id}>
                    {eq.nombre}
                  </option>
                ))}
              </select>
            </div>
          ))}
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
          onClick={handleNext}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700"
        >
          Siguiente
        </button>
      </div>
    </div>
  )
}
