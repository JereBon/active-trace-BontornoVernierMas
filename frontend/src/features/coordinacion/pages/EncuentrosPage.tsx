// features/coordinacion/pages/EncuentrosPage.tsx
import { useState } from 'react'
import { TablaEncuentros } from '../components/encuentros/TablaEncuentros'
import { EncuentroForm } from '../components/encuentros/EncuentroForm'
import { useCreateSlot } from '../hooks/useEncuentros'
import { exportarHtmlEncuentros } from '../services/encuentrosService'
import type { SlotCreate, InstanciaEncuentro } from '../types'

export function EncuentrosPage() {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<InstanciaEncuentro | null>(null)
  const [exporting, setExporting] = useState(false)
  const createSlot = useCreateSlot()

  const handleSubmit = (data: SlotCreate) => {
    createSlot.mutate(data, { onSuccess: () => setShowForm(false) })
  }

  const handleExportHtml = async () => {
    setExporting(true)
    try {
      const html = await exportarHtmlEncuentros()
      const blob = new Blob([html], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'encuentros.html'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      alert('Error al exportar el HTML.')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Encuentros</h2>
        <div className="flex gap-2">
          <button onClick={handleExportHtml} disabled={exporting} className="px-3 py-1.5 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50 disabled:opacity-40">
            {exporting ? 'Exportando…' : 'Exportar HTML'}
          </button>
          <button onClick={() => { setEditing(null); setShowForm(true) }} className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
            Nuevo Encuentro
          </button>
        </div>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Nuevo Encuentro</h3>
          <EncuentroForm
            onSubmit={handleSubmit}
            onCancel={() => setShowForm(false)}
            isLoading={createSlot.isPending}
          />
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <TablaEncuentros onEdit={(e) => setEditing(e)} />
      </div>
    </div>
  )
}
