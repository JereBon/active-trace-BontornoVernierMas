import { useAuth } from '@/features/auth/hooks/useAuth'

export function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6 shadow-sm">
      {/* Brand */}
      <span className="text-lg font-bold text-brand-700">activia-trace</span>

      {/* User info + logout */}
      <div className="flex items-center gap-4">
        {user && (
          <span className="text-sm text-gray-600">
            {user.full_name || user.email}
          </span>
        )}
        <button
          onClick={logout}
          className="rounded-lg px-3 py-1.5 text-sm text-gray-600 transition hover:bg-gray-100 hover:text-gray-900"
        >
          Cerrar sesión
        </button>
      </div>
    </header>
  )
}
