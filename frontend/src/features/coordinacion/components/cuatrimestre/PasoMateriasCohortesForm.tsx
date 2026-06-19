import { useState } from 'react'
import { useMaterias, useCohortes } from '../../../admin/hooks/useEstructura'
import type { Materia, Cohorte } from '../../../admin/types'

interface Props {
  onNext: (data: { materias: Materia[]; cohortes: Cohorte[] }) => void
}

export function PasoMateriasCohortesForm({ onNext }: Props) {
  const { data: materias = [], isLoading: loadingMaterias } = useMaterias()
  const { data: cohortes = [], isLoading: loadingCohortes } = useCohortes()
  const [selectedMaterias, setSelectedMaterias] = useState<string[]>([])
  const [selectedCohortes, setSelectedCohortes] = useState<string[]>([])

  const toggleMateria = (id: string) => {
    setSelectedMaterias((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const toggleCohorte = (id: string) => {
    setSelectedCohortes((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const handleNext = () => {
    if (selectedMaterias.length === 0) return
    if (selectedCohortes.length === 0) return
    const materiasSel = materias.filter((m) => selectedMaterias.includes(m.id))
    const cohortesSel = cohortes.filter((c) => selectedCohortes.includes(c.id))
    onNext({ materias: materiasSel, cohortes: cohortesSel })
  }

  if (loadingMaterias || loadingCohortes) {
    return <div className="text-sm text-gray-400">Cargando catálogos...</div>
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-800">Paso 1: Materias y Cohortes</h3>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Materias del cuatrimestre
        </label>
        <div className="max-h-48 overflow-y-auto border border-gray-200 rounded p-2 space-y-1">
          {materias.length === 0 && (
            <p className="text-sm text-gray-400">No hay materias disponibles</p>
          )}
          {materias.map((m) => (
            <label key={m.id} className="flex items-center gap-2 py-1 cursor-pointer hover:bg-gray-50 rounded px-2">
              <input
                type="checkbox"
                checked={selectedMaterias.includes(m.id)}
                onChange={() => toggleMateria(m.id)}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-700">{m.nombre} ({m.codigo})</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Cohortes del cuatrimestre
        </label>
        <div className="max-h-48 overflow-y-auto border border-gray-200 rounded p-2 space-y-1">
          {cohortes.length === 0 && (
            <p className="text-sm text-gray-400">No hay cohortes disponibles</p>
          )}
          {cohortes.map((c) => (
            <label key={c.id} className="flex items-center gap-2 py-1 cursor-pointer hover:bg-gray-50 rounded px-2">
              <input
                type="checkbox"
                checked={selectedCohortes.includes(c.id)}
                onChange={() => toggleCohorte(c.id)}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-700">
                {c.carrera_nombre ?? '—'} — {c.nombre} (Año {c.anio})
              </span>
            </label>
          ))}
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleNext}
          disabled={selectedMaterias.length === 0 || selectedCohortes.length === 0}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Siguiente
        </button>
      </div>
    </div>
  )
}
