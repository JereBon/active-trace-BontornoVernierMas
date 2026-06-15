// features/coordinacion/pages/PadronCoordinacionPage.tsx
import { useRef, useState } from 'react'
import { useMaterias, useCohortes } from '@/features/admin/hooks/useEstructura'
import { usePreviewPadron, useConfirmarPadron, useVaciarPadron } from '../hooks/usePadron'
import type { EntradaPreview } from '../services/padronService'

export function PadronCoordinacionPage() {
  const [materiaId, setMateriaId] = useState('')
  const [cohorteId, setCohorteId] = useState('')
  const [preview, setPreview] = useState<EntradaPreview[] | null>(null)
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const { data: materias = [] } = useMaterias()
  const { data: cohortes = [] } = useCohortes()
  const previewMutation = usePreviewPadron()
  const confirmarMutation = useConfirmarPadron()
  const vaciarMutation = useVaciarPadron()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setMsg(null)
    setPreview(null)
    previewMutation.mutate(file, {
      onSuccess: (data) => setPreview(data),
      onError: () => setMsg({ type: 'error', text: 'Error al procesar el archivo.' }),
    })
  }

  const handleConfirmar = () => {
    if (!materiaId || !cohorteId || !preview) return
    confirmarMutation.mutate(
      { materia_id: materiaId, cohorte_id: cohorteId, entradas: preview },
      {
        onSuccess: () => {
          setMsg({ type: 'success', text: `${preview.length} alumnos importados correctamente.` })
          setPreview(null)
          if (fileRef.current) fileRef.current.value = ''
        },
        onError: () => setMsg({ type: 'error', text: 'Error al confirmar la importación.' }),
      },
    )
  }

  const handleVaciar = () => {
    if (!materiaId) return
    if (!window.confirm('¿Vaciar todo el padrón de esta materia? Esta acción no se puede deshacer.')) return
    vaciarMutation.mutate(materiaId, {
      onSuccess: () => setMsg({ type: 'success', text: 'Padrón vaciado correctamente.' }),
      onError: () => setMsg({ type: 'error', text: 'Error al vaciar el padrón.' }),
    })
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-800">Importar Padrón</h2>

      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Materia</label>
            <select
              value={materiaId}
              onChange={(e) => { setMateriaId(e.target.value); setPreview(null); setMsg(null) }}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
            >
              <option value="">— Seleccioná una materia —</option>
              {materias.map((m) => (
                <option key={m.id} value={m.id}>{m.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte</label>
            <select
              value={cohorteId}
              onChange={(e) => setCohorteId(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
            >
              <option value="">— Seleccioná una cohorte —</option>
              {cohortes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.anio}{c.plan ? ` (${c.plan})` : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Archivo CSV</label>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            disabled={!materiaId || previewMutation.isPending}
            className="text-sm file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
          />
          {previewMutation.isPending && (
            <p className="text-xs text-gray-500 mt-1">Procesando archivo…</p>
          )}
        </div>

        {msg && (
          <p className={`text-sm px-3 py-2 rounded border ${msg.type === 'success' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-600 border-red-200'}`}>
            {msg.text}
          </p>
        )}

        <div className="flex justify-between items-center pt-2 border-t border-gray-100">
          <button
            onClick={handleVaciar}
            disabled={!materiaId || vaciarMutation.isPending}
            className="px-3 py-1.5 text-sm text-red-600 border border-red-300 rounded hover:bg-red-50 disabled:opacity-40"
          >
            {vaciarMutation.isPending ? 'Vaciando…' : 'Vaciar Padrón'}
          </button>
          {preview !== null && (
            <button
              onClick={handleConfirmar}
              disabled={!materiaId || !cohorteId || confirmarMutation.isPending}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {confirmarMutation.isPending ? 'Importando…' : `Confirmar ${preview.length} alumnos`}
            </button>
          )}
        </div>
      </div>

      {preview && preview.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Vista previa — {preview.length} registros
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Apellidos</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Nombre</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Email</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Comisión</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {preview.slice(0, 20).map((e, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-3 py-1.5 text-gray-700">{e.apellidos}</td>
                    <td className="px-3 py-1.5 text-gray-700">{e.nombre}</td>
                    <td className="px-3 py-1.5 text-gray-500 font-mono text-xs">{e.email}</td>
                    <td className="px-3 py-1.5 text-gray-500">{e.comision ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {preview.length > 20 && (
              <p className="text-xs text-gray-400 mt-2 px-3">… y {preview.length - 20} registros más.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
