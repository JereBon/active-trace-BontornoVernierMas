// features/coordinacion/pages/CoordinacionLayout.tsx
import { NavLink, Outlet } from 'react-router-dom'

const TAB_ITEMS = [
  { to: '/coordinacion/equipos', label: 'Equipos' },
  { to: '/coordinacion/avisos', label: 'Avisos' },
  { to: '/coordinacion/tareas', label: 'Tareas' },
  { to: '/coordinacion/monitor', label: 'Monitor' },
  { to: '/coordinacion/encuentros', label: 'Encuentros' },
  { to: '/coordinacion/coloquios', label: 'Coloquios' },
  { to: '/coordinacion/cuatrimestre', label: 'Cuatrimestre' },
]

export function CoordinacionLayout() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Coordinación</h1>
        <p className="text-sm text-gray-500 mt-1">
          Gestión de equipos, avisos, tareas y configuración académica.
        </p>
      </div>

      {/* Horizontal tab nav */}
      <nav className="flex gap-1 border-b border-gray-200">
        {TAB_ITEMS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              [
                'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
                isActive
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              ].join(' ')
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      <div>
        <Outlet />
      </div>
    </div>
  )
}
