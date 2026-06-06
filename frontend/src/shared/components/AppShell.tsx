import { NavLink, Outlet } from 'react-router-dom'
import { Navbar } from '@/shared/components/Navbar'

const SIDEBAR_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  // Comision requires a materiaId — navigating to monitor (no materia filter)
  // is the entry point for COORDINADOR/ADMIN to see all.
  { to: '/comision/placeholder/monitor', label: 'Comisión' },
]

export function AppShell() {
  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        {/* Main sidebar */}
        <aside className="hidden w-56 flex-col border-r border-gray-200 bg-white px-4 py-6 md:flex">
          <nav className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              Menú
            </p>
            {SIDEBAR_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  [
                    'mt-1 flex items-center rounded-md px-3 py-2 text-sm transition-colors',
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
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
