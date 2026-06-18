// features/finanzas/components/TablaFacturas.tsx
// Lista de facturas con filtros, creación y cambio de estado Pendiente→Abonada
import { useState } from 'react'
import { useCambiarEstadoFactura, useCreateFactura, useFacturas } from '../hooks/useFacturas'
import type { Factura, FacturaCreate, FacturaEstado, FacturaFiltros } from '../types'

const ESTADOS: Array<{ value: FacturaEstado | ''; label: string }> = [
  { value: '', label: 'Todos' },
  { value: 'pendiente', label: 'Pendiente' },
  { value: 'abonada', label: 'Abonada' },
]

interface RowProps {
  factura: Factura
}

function FilaFactura({ factura }: RowProps) {
  const cambiar = useCambiarEstadoFactura()

  function handleAbonar() {
    if (factura.estado !== 'pendiente') return
    cambiar.mutate({ id: factura.id, estado: 'abonada' })
  }

  return (
    <tr className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
      <td className="py-3 px-4 text-sm text-gray-900">{factura.nombre_docente}</td>
      <td className="py-3 px-4 text-sm text-gray-600">{factura.periodo}</td>
      <td className="py-3 px-4 text-sm text-right text-gray-900">
        ${factura.monto.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
      </td>
      <td className="py-3 px-4 text-sm">{factura.numero ?? '—'}</td>
      <td className="py-3 px-4 text-sm">{factura.fecha_emision ?? '—'}</td>
      <td className="py-3 px-4 text-sm">
        <span
          className={[
            'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
            factura.estado === 'abonada'
              ? 'bg-green-100 text-green-700'
              : 'bg-yellow-100 text-yellow-700',
          ].join(' ')}
        >
          {factura.estado}
        </span>
      </td>
      <td className="py-3 px-4 text-sm">
        {factura.estado === 'pendiente' && (
          <button
            onClick={handleAbonar}
            disabled={cambiar.isPending}
            className="rounded bg-green-600 px-2 py-1 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            Marcar abonada
          </button>
        )}
      </td>
    </tr>
  )
}

export function TablaFacturas() {
  const [filtros, setFiltros] = useState<FacturaFiltros>({})
  const [estadoInput, setEstadoInput] = useState<FacturaEstado | ''>('')
  const [crearOpen, setCrearOpen] = useState(false)
  const [crearForm, setCrearForm] = useState<FacturaCreate>({
    usuario_id: '',
    periodo: '',
    monto: 0,
    numero: null,
    fecha_emision: null,
  })
  const create = useCreateFactura()

  const { data: facturas = [], isLoading } = useFacturas(filtros)

  function handleCrear() {
    create.mutate(crearForm, {
      onSuccess: () => {
        setCrearOpen(false)
        setCrearForm({ usuario_id: '', periodo: '', monto: 0, numero: null, fecha_emision: null })
      },
    })
  }

  function aplicarFiltros() {
    setFiltros({
      ...filtros,
      estado: estadoInput || undefined,
    })
  }

  return (
    <div className="space-y-4">
      {/* Crear factura */}
      <div className="flex justify-end">
        <button
          onClick={() => setCrearOpen(true)}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          + Nueva factura
        </button>
      </div>

      {crearOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-bold text-gray-900">Nueva factura</h2>
            <div className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600">Usuario ID</label>
                <input
                  type="text"
                  value={crearForm.usuario_id}
                  onChange={(e) => setCrearForm((f) => ({ ...f, usuario_id: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600">Período (YYYY-MM)</label>
                <input
                  type="text"
                  value={crearForm.periodo}
                  onChange={(e) => setCrearForm((f) => ({ ...f, periodo: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600">Monto</label>
                <input
                  type="number"
                  step="0.01"
                  value={crearForm.monto}
                  onChange={(e) => setCrearForm((f) => ({ ...f, monto: Number(e.target.value) }))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600">N° Factura</label>
                <input
                  type="text"
                  value={crearForm.numero ?? ''}
                  onChange={(e) => setCrearForm((f) => ({ ...f, numero: e.target.value || null }))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600">Fecha emisión</label>
                <input
                  type="date"
                  value={crearForm.fecha_emision ?? ''}
                  onChange={(e) => setCrearForm((f) => ({ ...f, fecha_emision: e.target.value || null }))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-3">
              <button
                onClick={() => setCrearOpen(false)}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleCrear}
                disabled={create.isPending || !crearForm.usuario_id || !crearForm.periodo || crearForm.monto <= 0}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {create.isPending ? 'Creando…' : 'Crear factura'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <div>
          <label className="block text-xs font-medium text-gray-600">Estado</label>
          <select
            value={estadoInput}
            onChange={(e) => setEstadoInput(e.target.value as FacturaEstado | '')}
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {ESTADOS.map((op) => (
              <option key={op.value} value={op.value}>
                {op.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Período (YYYY-MM)</label>
          <input
            type="text"
            placeholder="2024-03"
            value={filtros.periodo ?? ''}
            onChange={(e) => setFiltros((f) => ({ ...f, periodo: e.target.value || undefined }))}
            className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={aplicarFiltros}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Filtrar
        </button>
      </div>

      {/* Tabla */}
      {isLoading ? (
        <p className="text-sm text-gray-400">Cargando facturas…</p>
      ) : facturas.length === 0 ? (
        <p className="text-sm text-gray-400">No hay facturas con los filtros seleccionados.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-left">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Docente</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Período</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-right text-gray-500">Monto</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">N° Factura</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Emisión</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Estado</th>
                <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {facturas.map((f) => (
                <FilaFactura key={f.id} factura={f} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
