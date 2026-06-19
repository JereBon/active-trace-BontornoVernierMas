import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getPerfil, updatePerfil } from '../services/perfilService'
import type { PerfilUpdate } from '../services/perfilService'

const PERFIL_KEY = ['perfil']

export function usePerfil() {
  return useQuery({ queryKey: PERFIL_KEY, queryFn: getPerfil })
}

export function useUpdatePerfil() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: PerfilUpdate) => updatePerfil(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: PERFIL_KEY }),
  })
}
