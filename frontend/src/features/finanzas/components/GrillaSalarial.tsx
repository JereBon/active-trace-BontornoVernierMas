// features/finanzas/components/GrillaSalarial.tsx
// ABM de SalarioBase y SalarioPlus
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  useCreateSalarioBase,
  useCreateSalarioPlus,
  useSalariosBase,
  useSalariosPlus,
} from '../hooks/useGrilla'
import type { SalarioBase, SalarioPlus } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const salarioBaseSchema = z.object({
  rol: z.string().min(1, 'Rol requerido'),
  monto: z.coerce.number().positive('Debe ser positivo'),
  vigencia_desde: z.string().min(1, 'Fecha requerida'),
  vigencia_hasta: z.string().optional(),
})

const salarioPlusSchema = z.object({
  grupo: z.string().min(1, 'Grupo requerido'),
  rol: z.string().min(1, 'Rol requerido'),
  monto: z.coerce.number().positive('Debe ser positivo'),
  vigencia_desde: z.string().min(1, 'Fecha requerida'),
  vigencia_hasta: z.string().optional(),
})

type SalarioBaseForm = z.infer<typeof salarioBaseSchema>
type SalarioPlusForm = z.infer<typeof salarioPlusSchema>

// ─── Tabla SalarioBase ────────────────────────────────────────────────────────

function TablaSalarioBase({ rows }: { rows: SalarioBase[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-gray-400">Sin registros de salario base.</p>
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-left">
        <thead className="bg-gray-50">
          <tr>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Rol</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-right text-gray-500">Monto</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Vigencia desde</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Vigencia hasta</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
              <td className="py-3 px-4 text-sm font-medium text-gray-900">{row.rol}</td>
              <td className="py-3 px-4 text-sm text-right text-gray-900">
                ${row.monto.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3 px-4 text-sm text-gray-600">{row.vigencia_desde}</td>
              <td className="py-3 px-4 text-sm text-gray-600">{row.vigencia_hasta ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Form SalarioBase ─────────────────────────────────────────────────────────

function FormSalarioBase({ onClose }: { onClose: () => void }) {
  const create = useCreateSalarioBase()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SalarioBaseForm>({ resolver: zodResolver(salarioBaseSchema) })

  function onSubmit(values: SalarioBaseForm) {
    create.mutate(values, { onSuccess: onClose })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h4 className="text-sm font-semibold text-gray-700">Nuevo SalarioBase</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600">Rol</label>
          <input
            {...register('rol')}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="PROFESOR"
          />
          {errors.rol && <p className="mt-1 text-xs text-red-500">{errors.rol.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Monto</label>
          <input
            {...register('monto')}
            type="number"
            step="0.01"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.monto && <p className="mt-1 text-xs text-red-500">{errors.monto.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Vigencia desde</label>
          <input
            {...register('vigencia_desde')}
            type="date"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.vigencia_desde && (
            <p className="mt-1 text-xs text-red-500">{errors.vigencia_desde.message}</p>
          )}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Vigencia hasta</label>
          <input
            {...register('vigencia_hasta')}
            type="date"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={create.isPending}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {create.isPending ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}

// ─── Tabla SalarioPlus ────────────────────────────────────────────────────────

function TablaSalarioPlus({ rows }: { rows: SalarioPlus[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-gray-400">Sin registros de salario plus.</p>
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-left">
        <thead className="bg-gray-50">
          <tr>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Grupo</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Rol</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-right text-gray-500">Monto</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Vigencia desde</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Vigencia hasta</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
              <td className="py-3 px-4 text-sm text-gray-900">{row.grupo}</td>
              <td className="py-3 px-4 text-sm text-gray-900">{row.rol}</td>
              <td className="py-3 px-4 text-sm text-right text-gray-900">
                ${row.monto.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3 px-4 text-sm text-gray-600">{row.vigencia_desde}</td>
              <td className="py-3 px-4 text-sm text-gray-600">{row.vigencia_hasta ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Form SalarioPlus ─────────────────────────────────────────────────────────

function FormSalarioPlus({ onClose }: { onClose: () => void }) {
  const create = useCreateSalarioPlus()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SalarioPlusForm>({ resolver: zodResolver(salarioPlusSchema) })

  function onSubmit(values: SalarioPlusForm) {
    create.mutate(values, { onSuccess: onClose })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h4 className="text-sm font-semibold text-gray-700">Nuevo SalarioPlus</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600">Grupo</label>
          <input
            {...register('grupo')}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="MATEMATICA"
          />
          {errors.grupo && <p className="mt-1 text-xs text-red-500">{errors.grupo.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Rol</label>
          <input
            {...register('rol')}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="PROFESOR"
          />
          {errors.rol && <p className="mt-1 text-xs text-red-500">{errors.rol.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Monto</label>
          <input
            {...register('monto')}
            type="number"
            step="0.01"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.monto && <p className="mt-1 text-xs text-red-500">{errors.monto.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Vigencia desde</label>
          <input
            {...register('vigencia_desde')}
            type="date"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.vigencia_desde && (
            <p className="mt-1 text-xs text-red-500">{errors.vigencia_desde.message}</p>
          )}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Vigencia hasta</label>
          <input
            {...register('vigencia_hasta')}
            type="date"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={create.isPending}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {create.isPending ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}

// ─── GrillaSalarial (exported) ────────────────────────────────────────────────

export function GrillaSalarial() {
  const { data: bases = [], isLoading: loadingBase } = useSalariosBase()
  const { data: plus = [], isLoading: loadingPlus } = useSalariosPlus()
  const [showFormBase, setShowFormBase] = useState(false)
  const [showFormPlus, setShowFormPlus] = useState(false)

  return (
    <div className="space-y-8">
      {/* SalarioBase */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Salario Base</h2>
          <button
            onClick={() => setShowFormBase((v) => !v)}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            + Agregar
          </button>
        </div>
        {showFormBase && (
          <div className="mb-4">
            <FormSalarioBase onClose={() => setShowFormBase(false)} />
          </div>
        )}
        {loadingBase ? (
          <p className="text-sm text-gray-400">Cargando…</p>
        ) : (
          <TablaSalarioBase rows={bases} />
        )}
      </section>

      {/* SalarioPlus */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Salario Plus</h2>
          <button
            onClick={() => setShowFormPlus((v) => !v)}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            + Agregar
          </button>
        </div>
        {showFormPlus && (
          <div className="mb-4">
            <FormSalarioPlus onClose={() => setShowFormPlus(false)} />
          </div>
        )}
        {loadingPlus ? (
          <p className="text-sm text-gray-400">Cargando…</p>
        ) : (
          <TablaSalarioPlus rows={plus} />
        )}
      </section>
    </div>
  )
}
