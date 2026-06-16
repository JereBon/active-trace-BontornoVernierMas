// features/admin/components/TablaUsuarios.tsx
// Lista de usuarios del tenant: activar/desactivar, ver perfil
import { useToggleActivarUsuario, useUsuarios } from '../hooks/useUsuarios'
import type { Usuario } from '../types'

interface RowProps {
  usuario: Usuario
}

function FilaUsuario({ usuario }: RowProps) {
  const toggle = useToggleActivarUsuario()

  return (
    <tr className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
      <td className="py-3 px-4 text-sm font-medium text-gray-900">
        {usuario.apellidos}, {usuario.nombre}
      </td>
      <td className="py-3 px-4 text-sm text-gray-600">{usuario.email ?? '—'}</td>
      <td className="py-3 px-4 text-sm text-gray-600">{usuario.legajo ?? '—'}</td>
      <td className="py-3 px-4 text-sm">
        <div className="flex flex-wrap gap-1">
          {(usuario.roles ?? []).map((r) => (
            <span
              key={r}
              className="inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700"
            >
              {r}
            </span>
          ))}
        </div>
      </td>
      <td className="py-3 px-4 text-sm">
        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
          usuario.activo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
        }`}>
          {usuario.activo ? 'Activo' : 'Inactivo'}
        </span>
      </td>
      <td className="py-3 px-4 text-sm">
        <button
          onClick={() => toggle.mutate({ id: usuario.id, activo: !usuario.activo })}
          disabled={toggle.isPending}
          className={[
            'rounded px-2 py-1 text-xs font-medium text-white disabled:opacity-50',
            usuario.activo ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600',
          ].join(' ')}
        >
          {usuario.activo ? 'Desactivar' : 'Activar'}
        </button>
      </td>
    </tr>
  )
}

export function TablaUsuarios() {
  const { data: usuarios = [], isLoading } = useUsuarios()

  if (isLoading) {
    return <p className="text-sm text-gray-400">Cargando usuarios…</p>
  }

  if (usuarios.length === 0) {
    return <p className="text-sm text-gray-400">No hay usuarios registrados en este tenant.</p>
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-left">
        <thead className="bg-gray-50">
          <tr>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Nombre</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Email</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Legajo</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Roles</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Estado</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map((u) => (
            <FilaUsuario key={u.id} usuario={u} />
          ))}
        </tbody>
      </table>
    </div>
  )
}
