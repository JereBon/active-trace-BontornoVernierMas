import { Outlet } from 'react-router-dom'
import { Navbar } from '@/shared/components/Navbar'

export function AppShell() {
  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar placeholder — populated in future feature modules */}
        <aside className="hidden w-56 flex-col border-r border-gray-200 bg-white px-4 py-6 md:flex">
          <nav className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              Menú
            </p>
            <p className="mt-2 text-sm text-gray-400 italic">
              Módulos próximamente…
            </p>
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
