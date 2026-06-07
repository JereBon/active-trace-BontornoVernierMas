// features/admin/services/usuariosService.ts
import { api } from '@/shared/services/api'
import type { Usuario } from '../types'

export async function getUsuarios(): Promise<Usuario[]> {
  const { data } = await api.get<Usuario[]>('/v1/usuarios')
  return data
}

export async function toggleActivarUsuario(
  id: string,
  activo: boolean,
): Promise<Usuario> {
  const { data } = await api.patch<Usuario>(`/v1/usuarios/${id}`, { activo })
  return data
}
