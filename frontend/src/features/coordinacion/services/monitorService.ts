import { api } from '@/shared/services/api'
import type { MonitorItem } from '@/features/comision/types'

export interface MonitorGlobalParams {
  materia_id?: string
  comision?: string
  regional?: string
  alumno_nombre?: string
  solo_atrasados?: boolean
  fecha_desde?: string
  fecha_hasta?: string
  limit?: number
  offset?: number
}

export async function getMonitorGlobal(params: MonitorGlobalParams = {}): Promise<MonitorItem[]> {
  const queryParams: Record<string, string> = {}
  if (params.materia_id) queryParams.materia_id = params.materia_id
  if (params.comision) queryParams.comision = params.comision
  if (params.regional) queryParams.regional = params.regional
  if (params.alumno_nombre) queryParams.alumno_nombre = params.alumno_nombre
  if (params.solo_atrasados) queryParams.solo_atrasados = 'true'
  if (params.fecha_desde) queryParams.fecha_desde = params.fecha_desde
  if (params.fecha_hasta) queryParams.fecha_hasta = params.fecha_hasta
  if (params.limit) queryParams.limit = String(params.limit)
  if (params.offset) queryParams.offset = String(params.offset)
  const { data } = await api.get<MonitorItem[]>('/v1/analisis/monitor', { params: queryParams })
  return data
}

export function exportMonitorToCsv(items: MonitorItem[]): void {
  const headers = ['Nombre', 'Apellidos', 'Comisión', 'Regional', 'Actividades', 'Aprobadas', 'No Aprobadas', 'Faltantes', 'Atrasado']
  const rows = items.map((i) => [
    `"${i.nombre}"`, `"${i.apellidos}"`, `"${i.comision ?? ''}"`, `"${i.regional ?? ''}"`,
    i.cant_actividades, i.cant_aprobadas, i.cant_no_aprobadas, i.cant_faltantes, i.es_atrasado ? 'Sí' : 'No',
  ])
  const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'monitor.csv'
  a.click()
  URL.revokeObjectURL(url)
}
