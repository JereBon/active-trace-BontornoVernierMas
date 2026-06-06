// features/comision/services/analisisService.ts
// All HTTP calls via the centralised Axios instance (JWT injected automatically).

import { api } from '@/shared/services/api'
import type {
  AtrasadoItem,
  MonitorItem,
  MonitorParams,
  NotaFinal,
  RankingItem,
  ReporteMateria,
  SinCorregirItem,
} from '../types'

/** GET /v1/analisis/atrasados?materia_id={materiaId} */
export async function getAtrasados(materiaId: string): Promise<AtrasadoItem[]> {
  const { data } = await api.get<AtrasadoItem[]>('/v1/analisis/atrasados', {
    params: { materia_id: materiaId },
  })
  return data
}

/** GET /v1/analisis/ranking?materia_id={materiaId} */
export async function getRanking(materiaId: string): Promise<RankingItem[]> {
  const { data } = await api.get<RankingItem[]>('/v1/analisis/ranking', {
    params: { materia_id: materiaId },
  })
  return data
}

/** GET /v1/analisis/notas-finales?materia_id={materiaId} */
export async function getNotasFinales(materiaId: string): Promise<NotaFinal[]> {
  const { data } = await api.get<NotaFinal[]>('/v1/analisis/notas-finales', {
    params: { materia_id: materiaId },
  })
  return data
}

/** GET /v1/analisis/reporte-materia?materia_id={materiaId} */
export async function getReporteMateria(materiaId: string): Promise<ReporteMateria> {
  const { data } = await api.get<ReporteMateria>('/v1/analisis/reporte-materia', {
    params: { materia_id: materiaId },
  })
  return data
}

/** GET /v1/analisis/sin-corregir?materia_id={materiaId} */
export async function getSinCorregir(materiaId: string): Promise<SinCorregirItem[]> {
  const { data } = await api.get<SinCorregirItem[]>('/v1/analisis/sin-corregir', {
    params: { materia_id: materiaId },
  })
  return data
}

/** GET /v1/analisis/monitor — with optional filters */
export async function getMonitor(params: MonitorParams): Promise<MonitorItem[]> {
  const { data } = await api.get<MonitorItem[]>('/v1/analisis/monitor', {
    params,
  })
  return data
}
