// features/coordinacion/components/cuatrimestre/ResumenCuatrimestre.tsx
interface Props {
  materias: string[]
  cohortes: string[]
  asignaciones: Record<string, string>
  onConfirm: () => void
  onBack: () => void
  isConfirming?: boolean
}

export function ResumenCuatrimestre({
  materias,
  cohortes,
  asignaciones,
  onConfirm,
  onBack,
  isConfirming,
}: Props) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-800">Paso 3: Confirmar Configuración</h3>

      <div className="bg-gray-50 rounded-lg p-4 space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Materias seleccionadas</h4>
          {materias.length === 0 ? (
            <p className="text-sm text-gray-400">Ninguna</p>
          ) : (
            <ul className="space-y-1">
              {materias.map((m) => (
                <li key={m} className="text-sm text-gray-700">
                  • {m} → Equipo: {asignaciones[m] ?? 'Sin asignar'}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Cohortes</h4>
          {cohortes.length === 0 ? (
            <p className="text-sm text-gray-400">Ninguna</p>
          ) : (
            <p className="text-sm text-gray-700">{cohortes.join(', ')}</p>
          )}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
        >
          Anterior
        </button>
        <button
          onClick={onConfirm}
          disabled={isConfirming}
          className="px-4 py-2 text-sm text-white bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
        >
          {isConfirming ? 'Confirmando...' : 'Confirmar Cuatrimestre'}
        </button>
      </div>
    </div>
  )
}
