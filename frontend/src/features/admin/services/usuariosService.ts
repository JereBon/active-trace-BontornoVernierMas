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
): Promise<Usuario> {
  if (!activo) {
    await api.put(`/v1/users/${id}/deactivate`)
    // deactivate returns 204 no content; refetch will get updated state
    return { id, activo: false } as unknown as Usuario
  }
  // reactivation: use PUT update with activo flag
  const { data } = await api.put<Usuario>(`/v1/users/${id}`, { activo: true })
  return data
}
