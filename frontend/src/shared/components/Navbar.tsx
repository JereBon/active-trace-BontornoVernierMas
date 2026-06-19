import { Link } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'

export function Navbar() {
  const { user, logout, impersonatingUserId, stopImpersonating } = useAuth()

  return (
    <>
      {impersonatingUserId && (
        <div className="flex h-10 items-center justify-center gap-3 bg-amber-400 px-4 text-sm font-medium text-amber-900">
          <span>Estás operando como usuario {impersonatingUserId.slice(0, 8)}…</span>
          <button
            onClick={stopImpersonating}
            className="rounded bg-amber-500 px-2 py-0.5 text-xs text-white hover:bg-amber-600"
          >
            Terminar impersonación
          </button>
        </div>
      )}

      <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6 shadow-sm">
        <Link to="/dashboard" className="text-lg font-bold text-brand-700">
          activia-trace
        </Link>

        <div className="flex items-center gap-4">
          {user && (
            <>
              <Link
                to="/perfil"
                className="text-sm text-gray-600 transition hover:text-gray-900"
              >
                {user.full_name || user.email}
              </Link>
              <button
                onClick={logout}
                className="rounded-lg px-3 py-1.5 text-sm text-gray-600 transition hover:bg-gray-100 hover:text-gray-900"
              >
                Cerrar sesión
              </button>
            </>
          )}
        </div>
      </header>
    </>
  )
}
