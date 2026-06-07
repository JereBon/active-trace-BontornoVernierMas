// features/admin/components/EstructuraAcademica.tsx
// ABM de Carreras, Cohortes y Materias (incluye categoria_clave)
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  useCarreras,
  useCohortes,
  useCreateCarrera,
  useCreateCohorte,
  useCreateMateria,
  useMaterias,
  useUpdateMateria,
} from '../hooks/useEstructura'
import type { Carrera, Cohorte, Materia } from '../types'

// ─── Schemas ──────────────────────────────────────────────────────────────────

const carreraSchema = z.object({
  nombre: z.string().min(1, 'Requerido'),
  codigo: z.string().min(1, 'Requerido'),
})

const cohorteSchema = z.object({
  carrera_id: z.string().uuid('UUID inválido'),
  anio: z.coerce.number().min(2000).max(2100),
  plan: z.string().optional(),
})

const materiaSchema = z.object({
  nombre: z.string().min(1, 'Requerido'),
  codigo: z.string().min(1, 'Requerido'),
  categoria_clave: z.string().optional(),
})

type CarreraForm = z.infer<typeof carreraSchema>
type CohorteForm = z.infer<typeof cohorteSchema>
type MateriaForm = z.infer<typeof materiaSchema>

// ─── Tabla Carreras ───────────────────────────────────────────────────────────

function TablaCarreras({ rows }: { rows: Carrera[] }) {
  if (rows.length === 0) return <p className="text-sm text-gray-400">Sin carreras registradas.</p>
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-left">
        <thead className="bg-gray-50">
          <tr>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Nombre</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Código</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Estado</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
              <td className="py-3 px-4 text-sm font-medium text-gray-900">{c.nombre}</td>
              <td className="py-3 px-4 text-sm text-gray-600">{c.codigo}</td>
              <td className="py-3 px-4 text-sm">
                <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                  c.activa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {c.activa ? 'Activa' : 'Inactiva'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Form Carrera ─────────────────────────────────────────────────────────────

function FormCarrera({ onClose }: { onClose: () => void }) {
  const create = useCreateCarrera()
  const { register, handleSubmit, formState: { errors } } = useForm<CarreraForm>({
    resolver: zodResolver(carreraSchema),
  })
  return (
    <form onSubmit={handleSubmit((v) => create.mutate(v, { onSuccess: onClose }))}
      className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h4 className="text-sm font-semibold text-gray-700">Nueva Carrera</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600">Nombre</label>
          <input {...register('nombre')} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          {errors.nombre && <p className="mt-1 text-xs text-red-500">{errors.nombre.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Código</label>
          <input {...register('codigo')} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          {errors.codigo && <p className="mt-1 text-xs text-red-500">{errors.codigo.message}</p>}
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onClose} className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700">Cancelar</button>
        <button type="submit" disabled={create.isPending} className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white disabled:opacity-50">
          {create.isPending ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}

// ─── Tabla Cohortes ───────────────────────────────────────────────────────────

function TablaCohortes({ rows }: { rows: Cohorte[] }) {
  if (rows.length === 0) return <p className="text-sm text-gray-400">Sin cohortes registradas.</p>
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-left">
        <thead className="bg-gray-50">
          <tr>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Carrera</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Año</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Plan</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Estado</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
              <td className="py-3 px-4 text-sm text-gray-900">{c.carrera_nombre ?? c.carrera_id}</td>
              <td className="py-3 px-4 text-sm text-gray-900">{c.anio}</td>
              <td className="py-3 px-4 text-sm text-gray-600">{c.plan ?? '—'}</td>
              <td className="py-3 px-4 text-sm">
                <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                  c.activa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {c.activa ? 'Activa' : 'Inactiva'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Form Cohorte ─────────────────────────────────────────────────────────────

function FormCohorte({ onClose }: { onClose: () => void }) {
  const create = useCreateCohorte()
  const { register, handleSubmit, formState: { errors } } = useForm<CohorteForm>({
    resolver: zodResolver(cohorteSchema),
  })
  return (
    <form onSubmit={handleSubmit((v) => create.mutate(v, { onSuccess: onClose }))}
      className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h4 className="text-sm font-semibold text-gray-700">Nueva Cohorte</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600">Carrera ID (UUID)</label>
          <input {...register('carrera_id')} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          {errors.carrera_id && <p className="mt-1 text-xs text-red-500">{errors.carrera_id.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Año</label>
          <input {...register('anio')} type="number" className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          {errors.anio && <p className="mt-1 text-xs text-red-500">{errors.anio.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Plan</label>
          <input {...register('plan')} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onClose} className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700">Cancelar</button>
        <button type="submit" disabled={create.isPending} className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white disabled:opacity-50">
          {create.isPending ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}

// ─── Tabla Materias ───────────────────────────────────────────────────────────

function TablaMaterias({ rows }: { rows: Materia[] }) {
  if (rows.length === 0) return <p className="text-sm text-gray-400">Sin materias registradas.</p>
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-left">
        <thead className="bg-gray-50">
          <tr>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Nombre</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Código</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Categoría clave</th>
            <th className="py-3 px-4 text-xs font-semibold uppercase text-gray-500">Estado</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((m) => (
            <tr key={m.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
              <td className="py-3 px-4 text-sm font-medium text-gray-900">{m.nombre}</td>
              <td className="py-3 px-4 text-sm text-gray-600">{m.codigo}</td>
              <td className="py-3 px-4 text-sm text-gray-600">{m.categoria_clave ?? '—'}</td>
              <td className="py-3 px-4 text-sm">
                <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                  m.activa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {m.activa ? 'Activa' : 'Inactiva'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Form Materia ─────────────────────────────────────────────────────────────

function FormMateria({ onClose }: { onClose: () => void }) {
  const create = useCreateMateria()
  const { register, handleSubmit, formState: { errors } } = useForm<MateriaForm>({
    resolver: zodResolver(materiaSchema),
  })
  return (
    <form onSubmit={handleSubmit((v) => create.mutate(v, { onSuccess: onClose }))}
      className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h4 className="text-sm font-semibold text-gray-700">Nueva Materia</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600">Nombre</label>
          <input {...register('nombre')} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          {errors.nombre && <p className="mt-1 text-xs text-red-500">{errors.nombre.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Código</label>
          <input {...register('codigo')} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          {errors.codigo && <p className="mt-1 text-xs text-red-500">{errors.codigo.message}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Categoría clave</label>
          <input {...register('categoria_clave')} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="ej: MATEMATICA" />
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onClose} className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700">Cancelar</button>
        <button type="submit" disabled={create.isPending} className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white disabled:opacity-50">
          {create.isPending ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}

// ─── EstructuraAcademica (exported) ───────────────────────────────────────────

export function EstructuraAcademica() {
  const { data: carreras = [], isLoading: lcr } = useCarreras()
  const { data: cohortes = [], isLoading: lco } = useCohortes()
  const { data: materias = [], isLoading: lma } = useMaterias()
  const [showCarrera, setShowCarrera] = useState(false)
  const [showCohorte, setShowCohorte] = useState(false)
  const [showMateria, setShowMateria] = useState(false)

  return (
    <div className="space-y-8">
      {/* Carreras */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Carreras</h2>
          <button onClick={() => setShowCarrera((v) => !v)}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700">
            + Agregar
          </button>
        </div>
        {showCarrera && <div className="mb-4"><FormCarrera onClose={() => setShowCarrera(false)} /></div>}
        {lcr ? <p className="text-sm text-gray-400">Cargando…</p> : <TablaCarreras rows={carreras} />}
      </section>

      {/* Cohortes */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Cohortes</h2>
          <button onClick={() => setShowCohorte((v) => !v)}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700">
            + Agregar
          </button>
        </div>
        {showCohorte && <div className="mb-4"><FormCohorte onClose={() => setShowCohorte(false)} /></div>}
        {lco ? <p className="text-sm text-gray-400">Cargando…</p> : <TablaCohortes rows={cohortes} />}
      </section>

      {/* Materias */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Materias</h2>
          <button onClick={() => setShowMateria((v) => !v)}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700">
            + Agregar
          </button>
        </div>
        {showMateria && <div className="mb-4"><FormMateria onClose={() => setShowMateria(false)} /></div>}
        {lma ? <p className="text-sm text-gray-400">Cargando…</p> : <TablaMaterias rows={materias} />}
      </section>
    </div>
  )
}
