// features/comision/pages/ImportacionPage.tsx
import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ImportarCalificacionesForm } from '../components/ImportarCalificacionesForm'
import { ActividadesSelector } from '../components/ActividadesSelector'
import { UmbralForm } from '../components/UmbralForm'
import { getMisAsignaciones } from '@/features/coordinacion/services/equiposService'
import { getMaterias } from '@/features/admin/services/estructuraService'
import type { CalificacionPreviewResponse, ImportarResponse } from '../types'

export function ImportacionPage() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const [asignacionId, setAsignacionId] = useState('')
  const [preview, setPreview] = useState<CalificacionPreviewResponse | null>(null)
  const [previewFile, setPreviewFile] = useState<File | null>(null)
  const [importResult, setImportResult] = useState<ImportarResponse | null>(null)

  const { data: todasAsignaciones = [], isLoading: loadingAsig } = useQuery({
    queryKey: ['mis-asignaciones'],
    queryFn: getMisAsignaciones,
  })

  const { data: materias = [] } = useQuery({
    queryKey: ['materias'],
    queryFn: getMaterias,
  })

  const materiaNombre = (id: string | null): string => {
    if (!id) return 'sin materia'
    const m = materias.find((m) => m.id === id)
    return m ? `${m.nombre} (${m.codigo})` : id.split('-').pop() ?? id
  }

  // Filter to assignments for this materia (or all if none match)
  const asignacionesMateria = materiaId
    ? todasAsignaciones.filter((a) => a.materia_id === materiaId)
    : todasAsignaciones

  const asignaciones = asignacionesMateria.length > 0 ? asignacionesMateria : todasAsignaciones

  // Auto-select when there's only one option
  useEffect(() => {
    if (asignaciones.length === 1 && !asignacionId) {
      setAsignacionId(asignaciones[0].id)
    }
  }, [asignaciones, asignacionId])

  if (!materiaId) return null

  function handlePreview(data: CalificacionPreviewResponse, file: File) {
    setPreview(data)
    setPreviewFile(file)
    setImportResult(null)
  }

  function handleImportado(result: ImportarResponse) {
    setImportResult(result)
    setPreview(null)
    setPreviewFile(null)
  }

  return (
    <div className="space-y-8 max-w-2xl">
      <h2 className="text-lg font-semibold text-gray-900">Calificaciones</h2>

      {/* Asignacion selector */}
      <div>
        <label htmlFor="asignacion-id" className="block text-sm font-medium text-gray-700">
          Tu cargo en la materia
        </label>
        {loadingAsig ? (
          <p className="mt-1 text-sm text-gray-400">Cargando asignaciones…</p>
        ) : asignaciones.length === 0 ? (
          <p className="mt-1 text-sm text-red-600">
            No tenés asignaciones registradas. Pedile al coordinador que te asigne a una materia.
          </p>
        ) : (
          <select
            id="asignacion-id"
            value={asignacionId}
            onChange={(e) => setAsignacionId(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">— Seleccioná tu asignación —</option>
            {asignaciones.map((a) => (
              <option key={a.id} value={a.id}>
                {materiaNombre(a.materia_id)} — {a.rol}
                {a.desde ? ` (desde ${a.desde.slice(0, 10)})` : ''}
              </option>
            ))}
          </select>
        )}
      </div>

      {importResult && (
        <div className="rounded-md bg-green-50 p-4 text-sm text-green-800">
          {importResult.mensaje} ({importResult.calificaciones_importadas} calificaciones)
        </div>
      )}

      {!preview && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-700">1. Subir calificaciones (exportación de Moodle)</h3>
          <p className="text-xs text-gray-500">
            El archivo debe ser el export de calificaciones de Moodle (.xlsx o .csv).
            Debe contener una columna <strong>Email address</strong> y columnas de notas con
            nombre que termine en <strong>(Real)</strong> para notas numéricas.
          </p>
          <ImportarCalificacionesForm
            materiaId={materiaId}
            onPreview={handlePreview}
          />
        </div>
      )}

      {preview && previewFile && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-700">2. Seleccionar actividades</h3>
          <p className="text-xs text-gray-500">
            Se detectaron {preview.actividades_numericas.length} numéricas y{' '}
            {preview.actividades_textuales.length} textuales.
          </p>
          <ActividadesSelector
            materiaId={materiaId}
            asignacionId={asignacionId}
            file={previewFile}
            preview={preview}
            onImportado={handleImportado}
          />
        </div>
      )}

      <hr className="border-gray-200" />

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-700">Umbral de aprobación</h3>
        <UmbralForm materiaId={materiaId} asignacionId={asignacionId} />
      </div>
    </div>
  )
}
