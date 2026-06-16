// features/comision/components/ImportarCalificacionesForm.tsx
// Dropzone for an LMS file. Calls /preview on submit and returns preview data.
import { useRef, useState } from 'react'
import { Spinner } from '@/shared/components/Spinner'
import { usePreviewCalificaciones } from '../hooks/useImportarCalificaciones'
import type { CalificacionPreviewResponse } from '../types'

interface Props {
  materiaId: string
  onPreview: (preview: CalificacionPreviewResponse, file: File) => void
}

export function ImportarCalificacionesForm({ materiaId, onPreview }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const preview = usePreviewCalificaciones()

  function handleFileChange(file: File) {
    setSelectedFile(file)
    preview.reset()
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFileChange(file)
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileChange(file)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedFile) return
    preview.mutate(
      { materiaId, file: selectedFile },
      { onSuccess: (data) => onPreview(data, selectedFile) },
    )
  }

  const errorMessage =
    preview.error instanceof Error ? preview.error.message : null

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Dropzone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Seleccionar archivo LMS"
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click() }}
        className={[
          'flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 cursor-pointer transition-colors',
          dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50 hover:border-blue-400',
        ].join(' ')}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.csv"
          className="hidden"
          onChange={handleInputChange}
          data-testid="file-input"
        />
        {selectedFile ? (
          <p className="text-sm font-medium text-gray-800">
            Archivo seleccionado: <span className="font-semibold">{selectedFile.name}</span>
          </p>
        ) : (
          <>
            <p className="text-sm text-gray-500">Arrastrá el archivo LMS aquí o hacé clic para seleccionarlo</p>
            <p className="mt-1 text-xs text-gray-400">Formatos aceptados: .xlsx, .csv</p>
          </>
        )}
      </div>

      {/* Error */}
      {errorMessage && (
        <p role="alert" className="text-sm text-red-600">
          {errorMessage}
        </p>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={!selectedFile || preview.isPending}
        className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {preview.isPending && <Spinner />}
        {preview.isPending ? 'Procesando…' : 'Vista previa'}
      </button>
    </form>
  )
}
