// features/dashboard/pages/DashboardPage.tsx
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'

interface QuickCard {
  title: string
  description: string
  path: string
  roles: string[]
  color: string
}

const CARDS: QuickCard[] = [
  {
    title: 'Comisión',
    description: 'Importar calificaciones, ver atrasados, enviar comunicaciones.',
    path: '/comision',
    roles: ['ADMIN', 'COORDINADOR', 'PROFESOR', 'TUTOR'],
    color: 'border-blue-200 hover:border-blue-400',
  },
  {
    title: 'Coordinación',
    description: 'Equipos docentes, avisos, tareas, encuentros, coloquios, guardias.',
    path: '/coordinacion',
    roles: ['ADMIN', 'COORDINADOR'],
    color: 'border-purple-200 hover:border-purple-400',
  },
  {
    title: 'Finanzas',
    description: 'Liquidaciones, grilla salarial, facturas y períodos.',
    path: '/finanzas',
    roles: ['FINANZAS'],
    color: 'border-green-200 hover:border-green-400',
  },
  {
    title: 'Administración',
    description: 'Estructura académica, usuarios, auditoría.',
    path: '/admin',
    roles: ['ADMIN'],
    color: 'border-red-200 hover:border-red-400',
  },
]

export function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const roles = user?.roles ?? []

  const visibleCards = CARDS.filter((c) =>
    c.roles.some((r) => roles.includes(r)),
  )

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">
          Bienvenido{user?.full_name ? `, ${user.full_name}` : ''}
        </h1>
        {roles.length > 0 && (
          <div className="flex gap-2 mt-2">
            {roles.map((r) => (
              <span
                key={r}
                className="inline-block rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
              >
                {r}
              </span>
            ))}
          </div>
        )}
      </div>

      {visibleCards.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {visibleCards.map((card) => (
            <button
              key={card.path}
              onClick={() => navigate(card.path)}
              className={`flex flex-col items-start gap-2 rounded-xl border-2 bg-white p-5 text-left shadow-sm transition ${card.color}`}
            >
              <h2 className="text-base font-semibold text-gray-900">{card.title}</h2>
              <p className="text-sm text-gray-500">{card.description}</p>
              <span className="mt-auto text-xs font-medium text-blue-600">Ir al módulo →</span>
            </button>
          ))}
        </div>
      ) : (
        <p className="text-gray-400 text-sm">No tenés módulos asignados a tu rol.</p>
      )}
    </div>
  )
}
