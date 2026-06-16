// features/admin/pages/AdminLayout.tsx
import { NavLink, Outlet } from 'react-router-dom'

const TAB_ITEMS = [
  { to: '/admin/estructura', label: 'Estructura académica' },
  { to: '/admin/usuarios', label: 'Usuarios' },
  { to: '/admin/auditoria', label: 'Auditoría' },
]

export function AdminLayout() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Administración</h1>
        <p className="mt-1 text-sm text-gray-500">
          Gestión de estructura académica, usuarios y auditoría del tenant.
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
