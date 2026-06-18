// features/coordinacion/services/cuatrimestreService.ts
import { api } from '@/shared/services/api'
import type {
  AsignacionCuatrimestre,
  AsignacionMasivaOut,
  AsignacionMasivaPayload,
} from '../types'

export async function confirmarCuatrimestre(
  asignaciones: AsignacionCuatrimestre[],
): Promise<AsignacionMasivaOut[]> {
  const results: AsignacionMasivaOut[] = []
  for (const a of asignaciones) {
    const payload: AsignacionMasivaPayload = {
      usuario_ids: [a.usuario_id],
      rol: a.rol,
      materia_id: a.materia_id,
      desde: a.desde,
      hasta: a.hasta,
    }
    const { data } = await api.post<AsignacionMasivaOut>(
      '/v1/equipos/asignacion-masiva',
      payload,
    )
    results.push(data)
  }
  return results
}
