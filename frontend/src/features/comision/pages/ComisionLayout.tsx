// features/comision/pages/ComisionLayout.tsx
// Secondary navigation layout for the comision feature.
import { NavLink, Outlet, useParams } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'

// F1.1: importar calificaciones → PROFESOR, COORDINADOR (no TUTOR)
// F3.2: comunicaciones → PROFESOR, COORDINADOR, ADMIN (no TUTOR)
const ROLES_IMPORTACION = ['PROFESOR', 'COORDINADOR', 'ADMIN']
const ROLES_COMUNICACION = ['PROFESOR', 'COORDINADOR', 'ADMIN']

export function ComisionLayout() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const { user } = useAuth()

  const puedeImportar = user?.roles?.some((r) => ROLES_IMPORTACION.includes(r)) ?? false
  const puedeComunicar = user?.roles?.some((r) => ROLES_COMUNICACION.includes(r)) ?? false

  const navItems = [
    ...(puedeImportar ? [{ to: 'importacion', label: 'Importación' }] : []),
    { to: 'atrasados', label: 'Atrasados' },
    { to: 'sin-corregir', label: 'Sin corregir' },
    ...(puedeComunicar ? [{ to: 'comunicacion', label: 'Comunicaciones' }] : []),
    { to: 'monitor', label: 'Monitor' },
  ]

  return (
    <div className="flex gap-6">
      {/* Secondary sidebar */}
      <nav className="hidden w-44 shrink-0 flex-col space-y-1 md:flex">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
          Comisión
        </p>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={`/comision/${materiaId ?? ''}/${item.to}`}
            className={({ isActive }) =>
              [
                'rounded-md px-3 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-blue-50 font-medium text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
              ].join(' ')
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Page content */}
      <div className="flex-1 overflow-auto">
        <Outlet />
      </div>
    </div>
  )
}
