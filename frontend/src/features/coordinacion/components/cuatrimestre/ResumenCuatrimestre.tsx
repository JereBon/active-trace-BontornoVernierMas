import type { Materia, Cohorte } from '../../../admin/types'
import type { AsignacionCuatrimestre } from '../../types'

interface Props {
  materias: Materia[]
  cohortes: Cohorte[]
  asignaciones: AsignacionCuatrimestre[]
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
      <h3 className="text-lg font-semibold text-gray-800">
        Paso 3: Confirmar Configuración
      </h3>

      <div className="bg-gray-50 rounded-lg p-4 space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">
            Materias seleccionadas ({materias.length})
          </h4>
          {materias.length === 0 ? (
            <p className="text-sm text-gray-400">Ninguna</p>
          ) : (
            <ul className="space-y-1">
              {materias.map((m) => (
                <li key={m.id} className="text-sm text-gray-700">
                  • {m.nombre} ({m.codigo})
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">
            Cohortes ({cohortes.length})
          </h4>
          {cohortes.length === 0 ? (
            <p className="text-sm text-gray-400">Ninguna</p>
          ) : (
            <ul className="space-y-1">
              {cohortes.map((c) => (
                <li key={c.id} className="text-sm text-gray-700">
                  • {c.carrera_nombre ?? '—'} — Año {c.anio}
                  {c.plan ? ` (${c.plan})` : ''}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">
            Asignaciones docentes ({asignaciones.length})
          </h4>
          {asignaciones.length === 0 ? (
            <p className="text-sm text-gray-400">Sin asignaciones</p>
          ) : (
            <ul className="space-y-1">
              {asignaciones.map((a) => {
                const materia = materias.find((m) => m.id === a.materia_id)
                return (
                  <li key={a.materia_id} className="text-sm text-gray-700">
                    • {materia?.nombre ?? a.materia_id} → {a.rol}
                    {a.hasta ? ` (${a.desde} — ${a.hasta})` : ` (desde ${a.desde})`}
                  </li>
                )
              })}
            </ul>
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
