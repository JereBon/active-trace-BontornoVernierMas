// features/coordinacion/components/cuatrimestre/PasoMateriasCohortesForm.tsx
import { useState } from 'react'
import { useCohortes, useMaterias } from '@/features/admin/hooks/useEstructura'

interface Props {
  onNext: (data: { materias: string[]; cohortes: string[] }) => void
}

export function PasoMateriasCohortesForm({ onNext }: Props) {
  const { data: materias = [], isLoading: lm } = useMaterias()
  const { data: cohortes = [], isLoading: lc } = useCohortes()

  const [selectedMaterias, setSelectedMaterias] = useState<string[]>([])
  const [selectedCohortes, setSelectedCohortes] = useState<string[]>([])

  const toggle = (list: string[], setList: (v: string[]) => void, id: string) => {
    setList(list.includes(id) ? list.filter((x) => x !== id) : [...list, id])
  }

  const handleNext = () => {
    if (selectedMaterias.length === 0 || selectedCohortes.length === 0) return
    onNext({ materias: selectedMaterias, cohortes: selectedCohortes })
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-800">Paso 1: Materias y Cohortes</h3>

      <div>
        <p className="block text-sm font-medium text-gray-700 mb-2">Materias</p>
        {lm ? (
          <p className="text-sm text-gray-400">Cargando...</p>
        ) : (
          <div className="space-y-1 max-h-48 overflow-y-auto border border-gray-200 rounded p-3">
            {materias.length === 0 ? (
              <p className="text-sm text-gray-400">No hay materias registradas.</p>
            ) : materias.map((m) => (
              <label key={m.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 px-1 py-0.5 rounded">
                <input
                  type="checkbox"
                  checked={selectedMaterias.includes(m.id)}
                  onChange={() => toggle(selectedMaterias, setSelectedMaterias, m.id)}
                  className="rounded"
                />
                <span className="text-gray-800">{m.nombre}</span>
                <span className="text-gray-400 text-xs">({m.codigo})</span>
              </label>
            ))}
          </div>
        )}
        {selectedMaterias.length > 0 && (
          <p className="text-xs text-blue-600 mt-1">{selectedMaterias.length} seleccionada(s)</p>
        )}
      </div>

      <div>
        <p className="block text-sm font-medium text-gray-700 mb-2">Cohortes</p>
        {lc ? (
          <p className="text-sm text-gray-400">Cargando...</p>
        ) : (
          <div className="space-y-1 max-h-48 overflow-y-auto border border-gray-200 rounded p-3">
            {cohortes.length === 0 ? (
              <p className="text-sm text-gray-400">No hay cohortes registradas.</p>
            ) : cohortes.map((c) => (
              <label key={c.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 px-1 py-0.5 rounded">
                <input
                  type="checkbox"
                  checked={selectedCohortes.includes(c.id)}
                  onChange={() => toggle(selectedCohortes, setSelectedCohortes, c.id)}
                  className="rounded"
                />
                <span className="text-gray-800">{c.nombre ?? c.anio}</span>
                <span className="text-gray-400 text-xs">— {c.carrera_nombre ?? ''}</span>
              </label>
            ))}
          </div>
        )}
        {selectedCohortes.length > 0 && (
          <p className="text-xs text-blue-600 mt-1">{selectedCohortes.length} seleccionada(s)</p>
        )}
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleNext}
          disabled={selectedMaterias.length === 0 || selectedCohortes.length === 0}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Siguiente
        </button>
      </div>
    </div>
  )
}
