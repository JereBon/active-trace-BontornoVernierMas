// features/coordinacion/hooks/useColoquios.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createColoquio, getColoquios } from '../services/coloquiosService'
import type { ColoquioCreate } from '../types'

const QUERY_KEY = ['coloquios']

export function useColoquios() {
  return useQuery({ queryKey: QUERY_KEY, queryFn: getColoquios })
}

export function useCreateColoquio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ColoquioCreate) => createColoquio(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
