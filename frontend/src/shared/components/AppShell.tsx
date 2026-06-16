import { NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Navbar } from '@/shared/components/Navbar'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { getMisAsignaciones } from '@/features/coordinacion/services/equiposService'

const COORDINACION_ROLES = ['COORDINADOR', 'ADMIN']
const FINANZAS_ROLES = ['FINANZAS', 'ADMIN']
const ADMIN_ROLES = ['ADMIN']

export function AppShell() {
  const { user, isAuthenticated } = useAuth()

  const isCoordinadorOrAdmin =
    user?.roles?.some((r) => COORDINACION_ROLES.includes(r)) ?? false
  const isFinanzas =
    user?.roles?.some((r) => FINANZAS_ROLES.includes(r)) ?? false
  const isAdmin =
    user?.roles?.some((r) => ADMIN_ROLES.includes(r)) ?? false

  const { data: asignaciones, isLoading: loadingAsignaciones } = useQuery({
    queryKey: ['mis-asignaciones'],
    queryFn: getMisAsignaciones,
    enabled: isAuthenticated,
  })
  const misComisiones = asignaciones
    ?.filter((a) => a.materia_id != null)
    .reduce<{ materiaId: string }[]>((acc, a) => {
      if (!acc.some((x) => x.materiaId === a.materia_id)) {
        acc.push({ materiaId: a.materia_id! })
      }
      return acc
    }, []) ?? []
  const tieneComision = !loadingAsignaciones && misComisiones.length > 0

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

            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                [
                  'mt-1 flex items-center rounded-md px-3 py-2 text-sm transition-colors',
                  isActive
                    ? 'bg-blue-50 font-medium text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                ].join(' ')
              }
            >
              Dashboard
            </NavLink>

            {tieneComision && misComisiones.map(({ materiaId }, i) => (
              <NavLink
                key={materiaId}
                to={`/comision/${materiaId}/monitor`}
                className={({ isActive }) =>
                  [
                    'mt-1 flex items-center rounded-md px-3 py-2 text-sm transition-colors',
                    isActive
                      ? 'bg-blue-50 font-medium text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                  ].join(' ')
                }
              >
                {misComisiones.length > 1 ? `Comisión ${i + 1}` : 'Comisión'}
              </NavLink>
            ))}

            {isCoordinadorOrAdmin && (
              <>
                <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Coordinación
                </p>
                <NavLink
                  to="/coordinacion"
                  className={({ isActive }) =>
                    [
                      'mt-1 flex items-center rounded-md px-3 py-2 text-sm transition-colors',
                      isActive
                        ? 'bg-blue-50 font-medium text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                    ].join(' ')
                  }
                >
                  Coordinación
                </NavLink>
              </>
            )}

            {isFinanzas && (
              <>
                <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Finanzas
                </p>
                <NavLink
                  to="/finanzas"
                  className={({ isActive }) =>
                    [
                      'mt-1 flex items-center rounded-md px-3 py-2 text-sm transition-colors',
                      isActive
                        ? 'bg-blue-50 font-medium text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                    ].join(' ')
                  }
                >
                  Finanzas
                </NavLink>
              </>
            )}

            {isAdmin && (
              <>
                <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Admin
                </p>
                <NavLink
                  to="/admin"
                  className={({ isActive }) =>
                    [
                      'mt-1 flex items-center rounded-md px-3 py-2 text-sm transition-colors',
                      isActive
                        ? 'bg-blue-50 font-medium text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                    ].join(' ')
                  }
                >
                  Administración
                </NavLink>
              </>
            )}
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
