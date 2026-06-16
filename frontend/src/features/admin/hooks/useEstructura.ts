// features/admin/hooks/useEstructura.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createCarrera,
  createCohorte,
  createMateria,
  deleteCarrera,
  getCarreras,
  getCohortes,
  getMaterias,
  updateCarrera,
  updateCohorte,
  updateMateria,
} from '../services/estructuraService'
import type {
  CarreraCreate,
  CarreraUpdate,
  CohorteCreate,
  CohorteUpdate,
  MateriaCreate,
  MateriaUpdate,
} from '../types'

const CARRERAS_KEY = ['carreras']
const COHORTES_KEY = ['cohortes']
const MATERIAS_KEY = ['materias']

export function useCarreras() {
  return useQuery({ queryKey: CARRERAS_KEY, queryFn: getCarreras })
}

export function useCreateCarrera() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: CarreraCreate) => createCarrera(p),
    onSuccess: () => qc.invalidateQueries({ queryKey: CARRERAS_KEY }),
  })
}

export function useUpdateCarrera() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CarreraUpdate }) =>
      updateCarrera(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: CARRERAS_KEY }),
  })
}

export function useDeleteCarrera() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteCarrera(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: CARRERAS_KEY }),
  })
}

export function useCohortes(carreraId?: string) {
  return useQuery({
    queryKey: [...COHORTES_KEY, carreraId],
    queryFn: () => getCohortes(carreraId),
  })
}

export function useCreateCohorte() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: CohorteCreate) => createCohorte(p),
    onSuccess: () => qc.invalidateQueries({ queryKey: COHORTES_KEY }),
  })
}

export function useUpdateCohorte() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CohorteUpdate }) =>
      updateCohorte(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: COHORTES_KEY }),
  })
}

export function useMaterias() {
  return useQuery({ queryKey: MATERIAS_KEY, queryFn: getMaterias })
}

export function useCreateMateria() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: MateriaCreate) => createMateria(p),
    onSuccess: () => qc.invalidateQueries({ queryKey: MATERIAS_KEY }),
  })
}

export function useUpdateMateria() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: MateriaUpdate }) =>
      updateMateria(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: MATERIAS_KEY }),
  })
}
