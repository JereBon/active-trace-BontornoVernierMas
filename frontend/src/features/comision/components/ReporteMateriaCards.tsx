// features/comision/components/ReporteMateriaCards.tsx
// Aggregate metric cards for a materia.
import { Spinner } from '@/shared/components/Spinner'
import { useReporteMateria } from '../hooks/useReporteMateria'

interface Props {
  materiaId: string
}

interface MetricCardProps {
  label: string
  value: string | number
  highlight?: boolean
}

function MetricCard({ label, value, highlight = false }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
      <p
        className={[
          'mt-1 text-2xl font-bold',
          highlight ? 'text-blue-600' : 'text-gray-900',
        ].join(' ')}
      >
        {value}
      </p>
    </div>
  )
}

export function ReporteMateriaCards({ materiaId }: Props) {
  const { data, isLoading, error } = useReporteMateria(materiaId)

  if (isLoading) return <Spinner />
  if (error) return <p className="text-sm text-red-600">{error.message}</p>
  if (!data) return null

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      <MetricCard label="Total alumnos" value={data.total_alumnos} />
      <MetricCard label="Actividades" value={data.total_actividades} />
      <MetricCard label="Con aprobada" value={data.alumnos_con_aprobada} />
      <MetricCard label="Atrasados" value={data.alumnos_atrasados} highlight />
      <MetricCard
        label="% Aprobación"
        value={`${data.porcentaje_aprobacion.toFixed(1)}%`}
        highlight
      />
    </div>
  )
}
