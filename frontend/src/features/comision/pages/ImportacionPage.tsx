// features/comision/pages/ImportacionPage.tsx
// Composes ImportarCalificacionesForm, ActividadesSelector, UmbralForm.
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { ImportarCalificacionesForm } from '../components/ImportarCalificacionesForm'
import { ActividadesSelector } from '../components/ActividadesSelector'
import { UmbralForm } from '../components/UmbralForm'
import type { CalificacionPreviewResponse, ImportarResponse } from '../types'

// TODO: In production, asignacionId comes from the authenticated user's assignment.
// For now, it is provided via a simple text input so the feature is functional without
// needing a separate user-assignments endpoint.
export function ImportacionPage() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const [asignacionId, setAsignacionId] = useState('')
  const [preview, setPreview] = useState<CalificacionPreviewResponse | null>(null)
  const [previewFile, setPreviewFile] = useState<File | null>(null)
  const [importResult, setImportResult] = useState<ImportarResponse | null>(null)

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
      <h2 className="text-lg font-semibold text-gray-900">Importación de calificaciones</h2>

      {/* Asignacion ID — transitional input until user profile endpoint is ready */}
      <div>
        <label htmlFor="asignacion-id" className="block text-sm font-medium text-gray-700">
          ID de asignación docente
        </label>
        <input
          id="asignacion-id"
          type="text"
          value={asignacionId}
          onChange={(e) => setAsignacionId(e.target.value)}
          placeholder="UUID de tu asignación"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
        <p className="mt-1 text-xs text-gray-400">
          Copiá tu ID de asignación desde el perfil docente.
        </p>
      </div>

      {importResult && (
        <div className="rounded-md bg-green-50 p-4 text-sm text-green-800">
          {importResult.mensaje} ({importResult.calificaciones_importadas} calificaciones)
        </div>
      )}

      {!preview && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-700">1. Subir archivo LMS</h3>
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
