// features/coordinacion/components/cuatrimestre/PasoMateriasCohortesForm.tsx
import { useState } from 'react'

interface Props {
  onNext: (data: { materias: string[]; cohortes: string[] }) => void
}

export function PasoMateriasCohortesForm({ onNext }: Props) {
  const [materiasInput, setMateriasInput] = useState('')
  const [cohortesInput, setCohortesInput] = useState('')

  const handleNext = () => {
    const materias = materiasInput
      .split(',')
      .map((m) => m.trim())
      .filter(Boolean)
    const cohortes = cohortesInput
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean)
    onNext({ materias, cohortes })
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-800">Paso 1: Materias y Cohortes</h3>

      <div>
        <label htmlFor="materias" className="block text-sm font-medium text-gray-700 mb-1">
          Materias (IDs separados por coma)
        </label>
        <input
          id="materias"
          value={materiasInput}
          onChange={(e) => setMateriasInput(e.target.value)}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="mat-001, mat-002, mat-003"
        />
      </div>

      <div>
        <label htmlFor="cohortes" className="block text-sm font-medium text-gray-700 mb-1">
          Cohortes (separadas por coma)
        </label>
        <input
          id="cohortes"
          value={cohortesInput}
          onChange={(e) => setCohortesInput(e.target.value)}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="2024A, 2024B"
        />
      </div>

      <div className="flex justify-end">
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
