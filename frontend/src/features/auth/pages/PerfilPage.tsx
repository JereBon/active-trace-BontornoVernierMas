import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { usePerfil, useUpdatePerfil } from '@/features/perfil/hooks/usePerfil'
import { Spinner } from '@/shared/components/Spinner'
import { getMisFacturas, crearMiFactura } from '@/features/perfil/services/perfilService'
import type { PerfilUpdate, FacturaMiaCreate } from '@/features/perfil/services/perfilService'

export function PerfilPage() {
  const { user } = useAuth()
  const { data: perfil, isLoading } = usePerfil()
  const updatePerfil = useUpdatePerfil()

  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [nombre, setNombre] = useState('')
  const [apellidos, setApellidos] = useState('')
  const [regional, setRegional] = useState('')
  const [banco, setBanco] = useState('')
  const [cbu, setCbu] = useState('')
  const [aliasCbu, setAliasCbu] = useState('')
  const [facturador, setFacturador] = useState(false)
  const [error, setError] = useState('')
  const [showFacturaForm, setShowFacturaForm] = useState(false)
  const [facturaPeriodo, setFacturaPeriodo] = useState('')
  const [facturaDetalle, setFacturaDetalle] = useState('')

  const { data: misFacturas = [], refetch: refetchFacturas } = useQuery({
    queryKey: ['mis-facturas'],
    queryFn: getMisFacturas,
    enabled: !!perfil?.facturador,
  })

  const crearFacturaMut = useMutation({
    mutationFn: (payload: FacturaMiaCreate) => crearMiFactura(payload),
    onSuccess: () => {
      setShowFacturaForm(false)
      setFacturaPeriodo('')
      setFacturaDetalle('')
      refetchFacturas()
    },
  })

  useEffect(() => {
    if (perfil) {
      setNombre(perfil.nombre ?? '')
      setApellidos(perfil.apellidos ?? '')
      setRegional(perfil.regional ?? '')
      setBanco(perfil.banco ?? '')
      setCbu(perfil.cbu ?? '')
      setAliasCbu(perfil.alias_cbu ?? '')
      setFacturador(perfil.facturador ?? false)
    }
  }, [perfil])

  const handleSave = async () => {
    setError('')
    const payload: PerfilUpdate = {
      nombre: nombre || null,
      apellidos: apellidos || null,
      regional: regional || null,
      banco: banco || null,
      cbu: cbu || null,
      alias_cbu: aliasCbu || null,
      facturador: facturador,
    }

    try {
      await updatePerfil.mutateAsync(payload)
      setEditing(false)
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : 'Error al guardar el perfil',
      )
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Mi Perfil</h1>
        <p className="mt-1 text-sm text-gray-500">
          Tus datos personales y configuración de seguridad.
        </p>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Información personal
          </h2>
          {!editing && (
            <button
              onClick={() => setEditing(true)}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-brand-600 hover:bg-brand-50"
            >
              Editar
            </button>
          )}
        </div>

        {editing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Nombre
                </label>
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Apellidos
                </label>
                <input
                  type="text"
                  value={apellidos}
                  onChange={(e) => setApellidos(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Regional
                </label>
                <input
                  type="text"
                  value={regional}
                  onChange={(e) => setRegional(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Banco
                </label>
                <input
                  type="text"
                  value={banco}
                  onChange={(e) => setBanco(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  CBU
                </label>
                <input
                  type="text"
                  value={cbu}
                  onChange={(e) => setCbu(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Alias CBU
                </label>
                <input
                  type="text"
                  value={aliasCbu}
                  onChange={(e) => setAliasCbu(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="facturador"
                checked={facturador}
                onChange={(e) => setFacturador(e.target.checked)}
                className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              />
              <label htmlFor="facturador" className="text-sm text-gray-700">
                Emito factura
              </label>
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 px-3 py-2">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleSave}
                disabled={updatePerfil.isPending}
                className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
              >
                {updatePerfil.isPending ? <Spinner size="sm" /> : null}
                {updatePerfil.isPending ? 'Guardando…' : 'Guardar'}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Nombre
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {[perfil?.nombre, perfil?.apellidos].filter(Boolean).join(' ') || '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Email
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {perfil?.email || user?.email || '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
                CUIL
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {perfil?.cuil || '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Legajo
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {perfil?.legajo || '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Regional
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {perfil?.regional || '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Roles
              </dt>
              <dd className="mt-1 flex flex-wrap gap-1">
                {(user?.roles ?? []).map((r) => (
                  <span
                    key={r}
                    className="inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700"
                  >
                    {r}
                  </span>
                ))}
              </dd>
            </div>
            {perfil?.banco && (
              <div>
                <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
                  Banco
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{perfil.banco}</dd>
              </div>
            )}
            {perfil?.cbu && (
              <div>
                <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
                  CBU
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{perfil.cbu}</dd>
              </div>
            )}
            {perfil?.alias_cbu && (
              <div>
                <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
                  Alias CBU
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{perfil.alias_cbu}</dd>
              </div>
            )}
          </dl>
        )}
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          Seguridad
        </h2>
        <p className="mb-4 text-sm text-gray-500">
          Configurá la autenticación en dos pasos para proteger tu cuenta.
        </p>
        <Link
          to="/perfil/2fa"
          className="inline-block rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Configurar 2FA
        </Link>
      </div>

      {perfil?.facturador && (
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Mis facturas</h2>
            <button
              onClick={() => setShowFacturaForm((v) => !v)}
              className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              {showFacturaForm ? 'Cancelar' : 'Subir factura'}
            </button>
          </div>

          {showFacturaForm && (
            <div className="mb-4 space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Período (AAAA-MM)</label>
                <input
                  type="text"
                  value={facturaPeriodo}
                  onChange={(e) => setFacturaPeriodo(e.target.value)}
                  placeholder="2026-06"
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Detalle (opcional)</label>
                <textarea
                  value={facturaDetalle}
                  onChange={(e) => setFacturaDetalle(e.target.value)}
                  rows={2}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              {crearFacturaMut.isError && (
                <p className="text-sm text-red-600">Error al subir la factura.</p>
              )}
              <div className="flex justify-end">
                <button
                  onClick={() => {
                    if (!facturaPeriodo.match(/^\d{4}-\d{2}$/)) return
                    crearFacturaMut.mutate({ periodo: facturaPeriodo, detalle: facturaDetalle || null })
                  }}
                  disabled={crearFacturaMut.isPending || !facturaPeriodo.match(/^\d{4}-\d{2}$/)}
                  className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                >
                  {crearFacturaMut.isPending ? 'Subiendo…' : 'Subir'}
                </button>
              </div>
            </div>
          )}

          {misFacturas.length === 0 ? (
            <p className="text-sm text-gray-400">No subiste facturas todavía.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">Período</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">Detalle</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">Estado</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">Subida</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {misFacturas.map((f) => (
                    <tr key={f.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-gray-700">{f.periodo}</td>
                      <td className="px-3 py-2 text-gray-500">{f.detalle ?? '—'}</td>
                      <td className="px-3 py-2">
                        <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${
                          f.estado === 'Abonada' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {f.estado}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-xs text-gray-400">
                        {f.cargada_at ? new Date(f.cargada_at).toLocaleDateString('es-AR') : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
