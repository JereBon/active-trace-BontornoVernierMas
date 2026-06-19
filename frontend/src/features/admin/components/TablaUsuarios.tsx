// features/admin/components/TablaUsuarios.tsx
import { useState } from 'react'
import { useCreateUsuario, useToggleActivarUsuario, useUsuarios } from '../hooks/useUsuarios'
import { useAuth } from '@/features/auth/hooks/useAuth'
import type { RolUsuario, Usuario } from '../types'

const ROLES_DISPONIBLES: { value: RolUsuario; label: string }[] = [
  { value: 'PROFESOR', label: 'Profesor' },
  { value: 'TUTOR', label: 'Tutor' },
  { value: 'COORDINADOR', label: 'Coordinador' },
  { value: 'NEXO', label: 'Nexo' },
  { value: 'FINANZAS', label: 'Finanzas' },
  { value: 'ADMIN', label: 'Admin' },
]

interface RowProps {
  usuario: Usuario
}

function FilaUsuario({ usuario }: RowProps) {
  const toggle = useToggleActivarUsuario()
  const { startImpersonation, user: currentUser } = useAuth()
  const [impersonating, setImpersonating] = useState(false)

  const canImpersonate = currentUser?.roles?.includes('ADMIN')
    && usuario.activo
    && usuario.id !== currentUser?.id

  const handleImpersonate = async () => {
    const name = [usuario.apellidos, usuario.nombre].filter(Boolean).join(', ') || usuario.email || usuario.id.slice(0, 8)
    const ok = window.confirm(`¿Estás seguro de que querés impersonar a ${name}? Vas a actuar como este usuario hasta que termines la sesión.`)
    if (!ok) return

    setImpersonating(true)
    try {
      await startImpersonation(usuario.id)
    } catch {
      setImpersonating(false)
    }
  }

  return (
    <tr className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
      <td className="py-3 px-4 text-sm font-medium text-gray-900">
        {[usuario.apellidos, usuario.nombre].filter(Boolean).join(', ') || '—'}
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
        <div className="flex items-center gap-2">
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

          {canImpersonate && (
            <button
              onClick={handleImpersonate}
              disabled={impersonating}
              className="rounded bg-amber-500 px-2 py-1 text-xs font-medium text-white hover:bg-amber-600 disabled:opacity-50"
            >
              {impersonating ? '…' : 'Impersonar'}
            </button>
          )}
        </div>
      </td>
    </tr>
  )
}

function FormCrearUsuario({ onClose }: { onClose: () => void }) {
  const create = useCreateUsuario()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [nombre, setNombre] = useState('')
  const [apellidos, setApellidos] = useState('')
  const [dni, setDni] = useState('')
  const [cuil, setCuil] = useState('')
  const [roles, setRoles] = useState<RolUsuario[]>([])

  const toggleRole = (r: RolUsuario) => {
    setRoles((prev) => (prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) return
    create.mutate(
      { email, password, nombre: nombre || null, apellidos: apellidos || null, dni: dni || null, cuil: cuil || null, roles },
      { onSuccess: onClose },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4 mb-4">
      <h4 className="text-sm font-semibold text-gray-700">Nuevo Usuario</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600">Email *</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Contraseña *</label>
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Nombre</label>
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Apellidos</label>
          <input value={apellidos} onChange={(e) => setApellidos(e.target.value)} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">DNI</label>
          <input value={dni} onChange={(e) => setDni(e.target.value)} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">CUIL</label>
          <input value={cuil} onChange={(e) => setCuil(e.target.value)} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Roles</label>
        <div className="flex flex-wrap gap-2">
          {ROLES_DISPONIBLES.map((r) => (
            <label key={r.value} className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={roles.includes(r.value)}
                onChange={() => toggleRole(r.value)}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-700">{r.label}</span>
            </label>
          ))}
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onClose} className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700">Cancelar</button>
        <button type="submit" disabled={create.isPending || !email || !password} className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white disabled:opacity-50">
          {create.isPending ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}

export function TablaUsuarios() {
  const { data: usuarios = [], isLoading } = useUsuarios()
  const [showForm, setShowForm] = useState(false)

  if (isLoading) {
    return <p className="text-sm text-gray-400">Cargando usuarios…</p>
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Usuarios</h2>
        <button onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700">
          + Nuevo usuario
        </button>
      </div>

      {showForm && <FormCrearUsuario onClose={() => setShowForm(false)} />}

      {usuarios.length === 0 ? (
        <p className="text-sm text-gray-400">No hay usuarios registrados en este tenant.</p>
      ) : (
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
      )}
    </div>
  )
}
