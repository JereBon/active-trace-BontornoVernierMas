import { useMutation } from '@tanstack/react-query'
import { confirmarCuatrimestre } from '../services/cuatrimestreService'
import type { AsignacionCuatrimestre } from '../types'

export function useConfirmarCuatrimestre() {
  return useMutation({
    mutationFn: (asignaciones: AsignacionCuatrimestre[]) =>
      confirmarCuatrimestre(asignaciones),
  })
}
