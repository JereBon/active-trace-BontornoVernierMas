// features/admin/hooks/useUsuarios.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getUsuarios, createUsuario, toggleActivarUsuario } from '../services/usuariosService'
import type { UsuarioCreate } from '../types'

const USUARIOS_KEY = ['admin-usuarios']

export function useUsuarios() {
  return useQuery({ queryKey: USUARIOS_KEY, queryFn: getUsuarios })
}

export function useCreateUsuario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: UsuarioCreate) => createUsuario(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: USUARIOS_KEY }),
  })
}

export function useToggleActivarUsuario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, activo }: { id: string; activo: boolean }) =>
      toggleActivarUsuario(id, activo),
    onSuccess: () => qc.invalidateQueries({ queryKey: USUARIOS_KEY }),
  })
}
