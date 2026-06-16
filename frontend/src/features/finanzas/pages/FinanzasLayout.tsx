// features/finanzas/pages/FinanzasLayout.tsx
import { NavLink, Outlet } from 'react-router-dom'

const TAB_ITEMS = [
  { to: '/finanzas/periodo', label: 'Período actual' },
  { to: '/finanzas/historial', label: 'Historial' },
  { to: '/finanzas/grilla', label: 'Grilla salarial' },
  { to: '/finanzas/facturas', label: 'Facturas' },
]

export function FinanzasLayout() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Finanzas</h1>
        <p className="mt-1 text-sm text-gray-500">
          Gestión de liquidaciones, grilla salarial y facturas.
        </p>
      </div>

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
