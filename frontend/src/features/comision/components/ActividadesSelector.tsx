// features/comision/components/ActividadesSelector.tsx
// Checkboxes for numeric/textual activities from the preview. Confirms import.
import { useState } from 'react'
import { Spinner } from '@/shared/components/Spinner'
import { useImportarCalificaciones } from '../hooks/useImportarCalificaciones'
import type { CalificacionPreviewResponse, ImportarResponse } from '../types'

interface Props {
  materiaId: string
  asignacionId: string
  file: File
  preview: CalificacionPreviewResponse
  onImportado: (result: ImportarResponse) => void
}

export function ActividadesSelector({
  materiaId,
  asignacionId,
  file,
  preview,
  onImportado,
}: Props) {
  const allActividades = [
    ...preview.actividades_numericas,
    ...preview.actividades_textuales,
  ]

  const [selected, setSelected] = useState<Set<string>>(new Set(allActividades))
  const [validationError, setValidationError] = useState<string | null>(null)

  const importar = useImportarCalificaciones()

  function toggle(actividad: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(actividad)) {
        next.delete(actividad)
      } else {
        next.add(actividad)
      }
      return next
    })
    setValidationError(null)
  }

  function handleConfirm() {
    if (selected.size === 0) {
      setValidationError('Seleccioná al menos una actividad para importar.')
      return
    }
    importar.mutate(
      {
        materiaId,
        asignacionId,
        file,
        actividadesSeleccionadas: Array.from(selected),
      },
      { onSuccess: (data) => onImportado(data) },
    )
  }

  const errorMessage =
    validationError ??
    (importar.error instanceof Error ? importar.error.message : null)

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-700">
        Seleccioná las actividades a importar
      </h3>

      {allActividades.length === 0 ? (
        <p className="text-sm text-gray-500">No se detectaron actividades en el archivo.</p>
      ) : (
        <div className="space-y-2 rounded-md border border-gray-200 bg-white p-4">
          {preview.actividades_numericas.length > 0 && (
            <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Numéricas</p>
          )}
          {preview.actividades_numericas.map((act) => (
            <label key={act} className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={selected.has(act)}
                onChange={() => toggle(act)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600"
              />
              {act}
            </label>
          ))}

          {preview.actividades_textuales.length > 0 && (
            <p className="mt-3 text-xs font-medium uppercase tracking-wide text-gray-400">Textuales</p>
          )}
          {preview.actividades_textuales.map((act) => (
            <label key={act} className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={selected.has(act)}
                onChange={() => toggle(act)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600"
              />
              {act}
            </label>
          ))}
        </div>
      )}

      {errorMessage && (
        <p role="alert" className="text-sm text-red-600">
          {errorMessage}
        </p>
      )}

      <button
        type="button"
        onClick={handleConfirm}
        disabled={importar.isPending}
        className="flex items-center gap-2 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {importar.isPending && <Spinner />}
        {importar.isPending ? 'Importando…' : 'Confirmar importación'}
      </button>
    </div>
  )
}
