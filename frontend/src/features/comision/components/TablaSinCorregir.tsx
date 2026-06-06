// features/comision/components/TablaSinCorregir.tsx
// Table of ungraded textual activities + CSV export (Blob + createObjectURL).
import { Spinner } from '@/shared/components/Spinner'
import { useSinCorregir } from '../hooks/useSinCorregir'
import type { SinCorregirItem } from '../types'

interface Props {
  materiaId: string
}

function buildCsv(items: SinCorregirItem[]): string {
  const header = 'Apellidos,Nombre,Comision,Actividad,Importado'
  const rows = items.map((item) =>
    [
      `"${item.apellidos}"`,
      `"${item.nombre}"`,
      `"${item.comision ?? ''}"`,
      `"${item.actividad}"`,
      `"${item.importado_at}"`,
    ].join(','),
  )
  return [header, ...rows].join('\n')
}

function downloadCsv(items: SinCorregirItem[]) {
  const csv = buildCsv(items)
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'sin_corregir.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export function TablaSinCorregir({ materiaId }: Props) {
  const { data, isLoading, error } = useSinCorregir(materiaId)

  if (isLoading) return <Spinner />
  if (error) return <p className="text-sm text-red-600">{error.message}</p>
  if (!data || data.length === 0)
    return <p className="text-sm text-gray-500">No hay entregas sin corregir.</p>

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500">
          {data.length} entrega{data.length !== 1 ? 's' : ''} sin corregir
        </p>
        <button
          type="button"
          onClick={() => downloadCsv(data)}
          disabled={data.length === 0}
          className="rounded-md bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-40"
          data-testid="export-csv-btn"
        >
          Exportar CSV
        </button>
      </div>
      <div className="overflow-x-auto rounded-md border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3 text-left">Nombre</th>
              <th className="px-4 py-3 text-left">Comisión</th>
              <th className="px-4 py-3 text-left">Actividad</th>
              <th className="px-4 py-3 text-left">Importado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {data.map((item, idx) => (
              <tr key={`${item.entrada_padron_id}-${idx}`} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">
                  {item.apellidos}, {item.nombre}
                </td>
                <td className="px-4 py-3 text-gray-600">{item.comision ?? '—'}</td>
                <td className="px-4 py-3 text-gray-700">{item.actividad}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {new Date(item.importado_at).toLocaleDateString('es-AR')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
