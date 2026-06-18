// features/comision/pages/ComisionIndexPage.tsx
// Selector de materia para entrar al módulo Comisión
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/services/api'

interface Materia {
  id: string
  nombre: string
  codigo: string
}

async function getMaterias(): Promise<Materia[]> {
  const { data } = await api.get<Materia[]>('/v1/materias')
  return data
}

export function ComisionIndexPage() {
  const navigate = useNavigate()
  const { data: materias = [], isLoading, error } = useQuery({
    queryKey: ['materias-selector'],
    queryFn: getMaterias,
  })

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-semibold text-gray-900">Comisión</h1>
        <p className="text-gray-400 text-sm">Cargando materias…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-semibold text-gray-900">Comisión</h1>
        <p className="text-red-500 text-sm">No se pudieron cargar las materias. Verificá que tengas permisos de estructura.</p>
      </div>
    )
  }

  if (materias.length === 0) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-semibold text-gray-900">Comisión</h1>
        <p className="text-gray-400 text-sm">No hay materias disponibles. Creá una en Admin → Estructura.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Comisión</h1>
        <p className="text-gray-500 text-sm mt-1">Seleccioná una materia para ver su comisión.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {materias.map((m) => (
          <button
            key={m.id}
            onClick={() => navigate(`/comision/${m.id}/atrasados`)}
            className="flex flex-col items-start gap-1 rounded-lg border border-gray-200 bg-white p-4 text-left shadow-sm transition hover:border-blue-400 hover:shadow"
          >
            <span className="text-xs font-mono text-gray-400">{m.codigo}</span>
            <span className="text-base font-medium text-gray-900">{m.nombre}</span>
            <span className="text-xs text-blue-600 mt-1">Ver comisión →</span>
          </button>
        ))}
      </div>
    </div>
  )
}
