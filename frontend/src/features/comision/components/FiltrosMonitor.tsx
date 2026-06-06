// features/comision/components/FiltrosMonitor.tsx
// Filter bar for the monitor view.
import { useState } from 'react'
import type { MonitorParams } from '../types'

interface Props {
  onBuscar: (params: MonitorParams) => void
}

export function FiltrosMonitor({ onBuscar }: Props) {
  const [alumno, setAlumno] = useState('')
  const [comision, setComision] = useState('')
  const [soloAtrasados, setSoloAtrasados] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const params: MonitorParams = {
      limit: 100,
      offset: 0,
    }
    if (alumno.trim()) params.alumno_nombre = alumno.trim()
    if (comision.trim()) params.comision = comision.trim()
    if (soloAtrasados) params.solo_atrasados = true
    onBuscar(params)
  }

  function handleReset() {
    setAlumno('')
    setComision('')
    setSoloAtrasados(false)
    onBuscar({ limit: 100, offset: 0 })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
      <div>
        <label htmlFor="monitor-alumno" className="block text-xs font-medium text-gray-600">
          Alumno
        </label>
        <input
          id="monitor-alumno"
          type="text"
          value={alumno}
          onChange={(e) => setAlumno(e.target.value)}
          placeholder="Nombre o apellido"
          className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>
      <div>
        <label htmlFor="monitor-comision" className="block text-xs font-medium text-gray-600">
          Comisión
        </label>
        <input
          id="monitor-comision"
          type="text"
          value={comision}
          onChange={(e) => setComision(e.target.value)}
          placeholder="Ej: 2024-A"
          className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>
      <label className="flex items-center gap-2 text-sm text-gray-700">
        <input
          type="checkbox"
          checked={soloAtrasados}
          onChange={(e) => setSoloAtrasados(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-blue-600"
        />
        Solo atrasados
      </label>
      <div className="flex gap-2">
        <button
          type="submit"
          className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          Buscar
        </button>
        <button
          type="button"
          onClick={handleReset}
          className="rounded-md border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-50"
        >
          Limpiar
        </button>
      </div>
    </form>
  )
}
