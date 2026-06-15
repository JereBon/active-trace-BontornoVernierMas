// features/coordinacion/hooks/usePadron.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { previewPadron, confirmarPadron, vaciarPadron } from '../services/padronService'
import type { ConfirmarPadronPayload } from '../services/padronService'

export function usePreviewPadron() {
  return useMutation({ mutationFn: (file: File) => previewPadron(file) })
}

export function useConfirmarPadron() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ConfirmarPadronPayload) => confirmarPadron(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['padron'] }),
  })
}

export function useVaciarPadron() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (materiaId: string) => vaciarPadron(materiaId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['padron'] }),
  })
}
