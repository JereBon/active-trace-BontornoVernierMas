import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createGuardia, exportarGuardias, getGuardias } from '../services/guardiasService'
import type { GuardiaCreate, GuardiaFilter } from '../services/guardiasService'

const QUERY_KEY = ['guardias']

export function useGuardias(filters?: GuardiaFilter) {
  return useQuery({
    queryKey: filters ? [...QUERY_KEY, filters] : QUERY_KEY,
    queryFn: () => getGuardias(filters),
  })
}

export function useCreateGuardia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: GuardiaCreate) => createGuardia(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
