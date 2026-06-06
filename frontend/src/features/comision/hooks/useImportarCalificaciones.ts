// features/comision/hooks/useImportarCalificaciones.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  previewCalificaciones,
  importarCalificaciones,
} from '../services/calificacionesService'
import type { CalificacionPreviewResponse, ImportarResponse } from '../types'

interface PreviewVars {
  materiaId: string
  file: File
}

interface ImportarVars {
  materiaId: string
  asignacionId: string
  file: File
  actividadesSeleccionadas: string[]
}

export function usePreviewCalificaciones() {
  return useMutation<CalificacionPreviewResponse, Error, PreviewVars>({
    mutationFn: ({ materiaId, file }) => previewCalificaciones(materiaId, file),
  })
}

export function useImportarCalificaciones() {
  const queryClient = useQueryClient()
  return useMutation<ImportarResponse, Error, ImportarVars>({
    mutationFn: ({ materiaId, asignacionId, file, actividadesSeleccionadas }) =>
      importarCalificaciones(materiaId, asignacionId, file, actividadesSeleccionadas),
    onSuccess: (_data, { materiaId }) => {
      // Invalidate analysis queries so they refetch after import
      void queryClient.invalidateQueries({ queryKey: ['atrasados', materiaId] })
      void queryClient.invalidateQueries({ queryKey: ['ranking', materiaId] })
      void queryClient.invalidateQueries({ queryKey: ['notas-finales', materiaId] })
      void queryClient.invalidateQueries({ queryKey: ['reporte-materia', materiaId] })
      void queryClient.invalidateQueries({ queryKey: ['sin-corregir', materiaId] })
    },
  })
}
