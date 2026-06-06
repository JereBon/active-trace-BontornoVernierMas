// features/comision/pages/SinCorregirPage.tsx
// Ungraded textual activities listing and CSV export.
import { useParams } from 'react-router-dom'
import { TablaSinCorregir } from '../components/TablaSinCorregir'

export function SinCorregirPage() {
  const { materiaId } = useParams<{ materiaId: string }>()
  if (!materiaId) return null

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Sin corregir</h2>
      <p className="text-sm text-gray-500">
        Entregas textuales finalizadas por el alumno que aún no tienen calificación registrada.
      </p>
      <TablaSinCorregir materiaId={materiaId} />
    </div>
  )
}
