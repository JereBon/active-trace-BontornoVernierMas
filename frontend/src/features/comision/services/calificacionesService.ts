// features/comision/services/calificacionesService.ts
// All HTTP calls via the centralised Axios instance (JWT injected automatically).

import { api } from '@/shared/services/api'
import type {
  CalificacionPreviewResponse,
  ImportarResponse,
  UmbralRequest,
  UmbralResponse,
} from '../types'

/**
 * POST /v1/calificaciones/{materiaId}/preview
 * Parse LMS file — no data is persisted.
 */
export async function previewCalificaciones(
  materiaId: string,
  file: File,
): Promise<CalificacionPreviewResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<CalificacionPreviewResponse>(
    `/v1/calificaciones/${materiaId}/preview`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

/**
 * POST /v1/calificaciones/{materiaId}/importar
 * Confirm import and persist calificaciones.
 * actividades_seleccionadas is sent as a JSON string in the multipart form.
 */
export async function importarCalificaciones(
  materiaId: string,
  asignacionId: string,
  file: File,
  actividadesSeleccionadas: string[],
): Promise<ImportarResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('asignacion_id', asignacionId)
  form.append('actividades_seleccionadas', JSON.stringify(actividadesSeleccionadas))
  const { data } = await api.post<ImportarResponse>(
    `/v1/calificaciones/${materiaId}/importar`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

/**
 * PUT /v1/calificaciones/{materiaId}/umbral
 * Configure passing threshold.
 */
export async function configurarUmbral(
  materiaId: string,
  body: UmbralRequest,
): Promise<UmbralResponse> {
  const { data } = await api.put<UmbralResponse>(
    `/v1/calificaciones/${materiaId}/umbral`,
    body,
  )
  return data
}
