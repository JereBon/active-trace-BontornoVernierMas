import { useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getCohortes } from '@/features/admin/services/estructuraService'
import {
  previewPadron,
  confirmarPadron,
  listarVersionesPadron,
  vaciarPadron,
  type EntradaPreview,
  type VersionPadron,
} from '../services/padronService'

export function PadronPage() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [cohorteId, setCohorteId] = useState('')
  const [preview, setPreview] = useState<EntradaPreview[] | null>(null)
  const [result, setResult] = useState<VersionPadron | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [confirmVaciar, setConfirmVaciar] = useState(false)

  const { data: cohortes = [] } = useQuery({
    queryKey: ['cohortes'],
    queryFn: () => getCohortes(),
  })

  const { data: versiones = [], refetch: refetchVersiones } = useQuery({
    queryKey: ['padron-versiones', materiaId],
    queryFn: () => listarVersionesPadron(materiaId!),
    enabled: !!materiaId,
  })

  const previewMutation = useMutation({
    mutationFn: (file: File) => previewPadron(file),
    onSuccess: (data) => {
      setPreview(data)
      setPreviewError(null)
      setResult(null)
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: { message?: string } } } })?.response?.data
          ?.detail?.message ?? 'Error al parsear el archivo.'
      setPreviewError(msg)
      setPreview(null)
    },
  })

  const confirmarMutation = useMutation({
    mutationFn: () => confirmarPadron(materiaId!, cohorteId, preview!),
    onSuccess: (data) => {
      setResult(data)
      setPreview(null)
      if (fileRef.current) fileRef.current.value = ''
      refetchVersiones()
    },
  })

  const vaciarMutation = useMutation({
    mutationFn: () => vaciarPadron(materiaId!),
    onSuccess: () => {
      setConfirmVaciar(false)
      setResult(null)
      refetchVersiones()
    },
  })

  if (!materiaId) return null

  function handlePreview() {
    const file = fileRef.current?.files?.[0]
    if (!file) return
    if (!cohorteId) {
      setPreviewError('Seleccioná una cohorte antes de continuar.')
      return
    }
    setPreviewError(null)
    previewMutation.mutate(file)
  }

  const activeVersion = versiones.find((v) => v.activa)

  return (
    <div className="space-y-8 max-w-2xl">
      <h2 className="text-lg font-semibold text-gray-900">Padrón de alumnos</h2>

      {activeVersion && (
        <div className="rounded-md bg-blue-50 border border-blue-200 p-3 text-sm text-blue-700">
          Versión activa cargada el{' '}
          {new Date(activeVersion.cargado_at).toLocaleDateString('es-AR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
          })}
          . Importar un nuevo archivo reemplazará esta versión.
        </div>
      )}

      {/* Step 1 — upload */}
      {!preview && !result && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Cohorte</label>
            <select
              value={cohorteId}
              onChange={(e) => setCohorteId(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">— Seleccioná la cohorte —</option>
              {cohortes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.carrera_nombre ?? 'Carrera'} — {c.anio}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Archivo de padrón</label>
            <p className="mt-0.5 text-xs text-gray-500">
              CSV o XLSX con columnas: <strong>nombre</strong>, <strong>apellidos</strong>,{' '}
              <strong>email</strong>, comision (opcional), regional (opcional).
            </p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv,.xlsx"
              className="mt-2 block w-full text-sm text-gray-600 file:mr-3 file:rounded-md file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          {previewError && (
            <p className="text-sm text-red-600">{previewError}</p>
          )}

          <button
            onClick={handlePreview}
            disabled={previewMutation.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {previewMutation.isPending ? 'Procesando…' : 'Vista previa'}
          </button>
        </div>
      )}

      {/* Step 2 — preview table */}
      {preview && (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Se encontraron <strong>{preview.length}</strong> alumnos. Revisá y confirmá.
          </p>
          <div className="overflow-x-auto rounded-md border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {['Apellidos', 'Nombre', 'Email', 'Comisión', 'Regional'].map((h) => (
                    <th
                      key={h}
                      className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {preview.map((e, i) => (
                  <tr key={i}>
                    <td className="px-3 py-2 text-gray-900">{e.apellidos}</td>
                    <td className="px-3 py-2 text-gray-900">{e.nombre}</td>
                    <td className="px-3 py-2 text-gray-500">{e.email}</td>
                    <td className="px-3 py-2 text-gray-500">{e.comision ?? '—'}</td>
                    <td className="px-3 py-2 text-gray-500">{e.regional ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {confirmarMutation.isError && (
            <p className="text-sm text-red-600">
              Error al confirmar. Verificá que la cohorte sea correcta.
            </p>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => {
                setPreview(null)
                if (fileRef.current) fileRef.current.value = ''
              }}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              onClick={() => confirmarMutation.mutate()}
              disabled={confirmarMutation.isPending}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {confirmarMutation.isPending ? 'Guardando…' : `Confirmar ${preview.length} alumnos`}
            </button>
          </div>
        </div>
      )}

      {/* Success */}
      {result && (
        <div className="space-y-4">
          <div className="rounded-md bg-green-50 border border-green-200 p-4 text-sm text-green-800">
            Padrón importado correctamente. Nueva versión activa desde{' '}
            {new Date(result.cargado_at).toLocaleDateString('es-AR', {
              day: '2-digit',
              month: '2-digit',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
            .
          </div>
          <button
            onClick={() => setResult(null)}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Importar otro padrón
          </button>
        </div>
      )}

      {/* Version history */}
      {versiones.length > 0 && !preview && !result && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-gray-700">Historial de versiones</h3>
            <button
              onClick={() => setConfirmVaciar(true)}
              className="text-xs px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50"
            >
              Vaciar datos
            </button>
          </div>
          <ul className="space-y-1">
            {versiones.map((v) => (
              <li key={v.id} className="flex items-center gap-2 text-xs text-gray-500">
                <span
                  className={`inline-block h-2 w-2 rounded-full ${v.activa ? 'bg-green-500' : 'bg-gray-300'}`}
                />
                {new Date(v.cargado_at).toLocaleString('es-AR')}
                {v.activa && (
                  <span className="text-green-600 font-medium">activa</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Confirm vaciar dialog */}
      {confirmVaciar && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">¿Vaciar padrón?</h3>
            <p className="text-sm text-gray-600 mb-4">
              Se van a eliminar todas las versiones y entradas del padrón de esta materia. Esta acción no se puede deshacer.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmVaciar(false)}
                className="px-4 py-2 text-sm border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => vaciarMutation.mutate()}
                disabled={vaciarMutation.isPending}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                {vaciarMutation.isPending ? 'Vaciando…' : 'Confirmar vaciado'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
