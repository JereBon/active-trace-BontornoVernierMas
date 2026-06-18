import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getUsuarios } from '../../services/equiposService'
import type { Materia } from '../../../admin/types'
import type { AsignacionCuatrimestre, RolAsignacion } from '../../types'

interface Props {
  materias: Materia[]
  onNext: (asignaciones: AsignacionCuatrimestre[]) => void
  onBack: () => void
}

export function PasoEquiposForm({ materias, onNext, onBack }: Props) {
  const { data: usuarios = [] } = useQuery({
    queryKey: ['usuarios'],
    queryFn: getUsuarios,
  })

  const [asignaciones, setAsignaciones] = useState<
    Record<string, { usuario_id: string; rol: RolAsignacion; desde: string; hasta: string }>
  >({})

  const updateAsignacion = (
    materiaId: string,
    field: string,
    value: string,
  ) => {
    setAsignaciones((prev) => ({
      ...prev,
      [materiaId]: {
        usuario_id: '',
        rol: 'PROFESOR',
        desde: new Date().toISOString().slice(0, 10),
        hasta: '',
        ...prev[materiaId],
        [field]: value,
      },
    }))
  }

  const handleNext = () => {
    const result: AsignacionCuatrimestre[] = materias
      .filter((m) => asignaciones[m.id]?.usuario_id)
      .map((m) => ({
        materia_id: m.id,
        usuario_id: asignaciones[m.id].usuario_id,
        rol: asignaciones[m.id].rol,
        desde: asignaciones[m.id].desde,
        hasta: asignaciones[m.id].hasta || null,
      }))
    onNext(result)
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-800">
        Paso 2: Asignación Docente
      </h3>

      {materias.length === 0 ? (
        <p className="text-gray-400 text-sm">No hay materias seleccionadas.</p>
      ) : (
        <div className="space-y-4">
          {materias.map((m) => {
            const val = asignaciones[m.id] ?? {}
            return (
              <div
                key={m.id}
                className="border border-gray-200 rounded p-4 space-y-3"
              >
                <p className="text-sm font-semibold text-gray-800">
                  {m.nombre} <span className="text-gray-400">({m.codigo})</span>
                </p>

                <div className="grid grid-cols-4 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Docente
                    </label>
                    <select
                      value={val.usuario_id ?? ''}
                      onChange={(e) =>
                        updateAsignacion(m.id, 'usuario_id', e.target.value)
                      }
                      className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                    >
                      <option value="">Seleccionar...</option>
                      {usuarios.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.nombre} {u.apellidos ?? ''}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Rol
                    </label>
                    <select
                      value={val.rol ?? 'PROFESOR'}
                      onChange={(e) =>
                        updateAsignacion(m.id, 'rol', e.target.value)
                      }
                      className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                    >
                      <option value="PROFESOR">PROFESOR</option>
                      <option value="TUTOR">TUTOR</option>
                      <option value="COORDINADOR">COORDINADOR</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Vigente desde
                    </label>
                    <input
                      type="date"
                      value={val.desde ?? ''}
                      onChange={(e) =>
                        updateAsignacion(m.id, 'desde', e.target.value)
                      }
                      className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Vigente hasta
                    </label>
                    <input
                      type="date"
                      value={val.hasta ?? ''}
                      onChange={(e) =>
                        updateAsignacion(m.id, 'hasta', e.target.value)
                      }
                      className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                    />
                  </div>
                </div>
              </div>
            )
          })}
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
          disabled={
            materias.length === 0 ||
            materias.every((m) => !asignaciones[m.id]?.usuario_id)
          }
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Siguiente
        </button>
      </div>
    </div>
  )
}
