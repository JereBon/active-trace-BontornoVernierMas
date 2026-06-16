// features/admin/services/usuariosService.ts
import { api } from '@/shared/services/api'
import type { Usuario } from '../types'

export async function getUsuarios(): Promise<Usuario[]> {
  const { data } = await api.get<Usuario[]>('/v1/users')
  return data
}

export async function toggleActivarUsuario(
  id: string,
  activo: boolean,
): Promise<void> {
  const endpoint = activo ? `/v1/users/${id}/activate` : `/v1/users/${id}/deactivate`
  await api.put(endpoint)
}
