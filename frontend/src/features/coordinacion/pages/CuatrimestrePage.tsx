// features/coordinacion/pages/CuatrimestrePage.tsx
import { useState } from 'react'
import { StepperCuatrimestre } from '../components/cuatrimestre/StepperCuatrimestre'
import { PasoMateriasCohortesForm } from '../components/cuatrimestre/PasoMateriasCohortesForm'
import { PasoEquiposForm } from '../components/cuatrimestre/PasoEquiposForm'
import { ResumenCuatrimestre } from '../components/cuatrimestre/ResumenCuatrimestre'
import { useClonarEquipo } from '../hooks/useEquipos'
import { useCohortes } from '@/features/admin/hooks/useEstructura'
import type { ClonarConfig } from '../components/cuatrimestre/PasoEquiposForm'

interface CuatrimestreState {
  materias: string[]
  cohortes: string[]
  clonarConfig: Record<string, ClonarConfig>
}

export function CuatrimestrePage() {
  const [step, setStep] = useState(0)
  const [isConfirming, setIsConfirming] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [state, setState] = useState<CuatrimestreState>({
    materias: [],
    cohortes: [],
    clonarConfig: {},
  })

  const clonarEquipo = useClonarEquipo()
  const { data: todasCohortes = [] } = useCohortes()

  const handlePaso1 = (data: { materias: string[]; cohortes: string[] }) => {
    setState((prev) => ({ ...prev, ...data, clonarConfig: {} }))
    setStep(1)
  }

  const handlePaso2 = (clonarConfig: Record<string, ClonarConfig>) => {
    setState((prev) => ({ ...prev, clonarConfig }))
    setStep(2)
  }

  const handleConfirm = async () => {
    setIsConfirming(true)
    setErrorMsg(null)

    try {
      const jobs: Array<Promise<unknown>> = []

      for (const materiaId of state.materias) {
        for (const cohorteDestinoId of state.cohortes) {
          const cfg = state.clonarConfig[cohorteDestinoId]
          if (!cfg?.origen_cohorte_id || !cfg?.desde) continue

          const cohorteDestino = todasCohortes.find((c) => c.id === cohorteDestinoId)
          const carreraId = cohorteDestino?.carrera_id
          if (!carreraId) continue

          jobs.push(
            clonarEquipo.mutateAsync({
              materia_id: materiaId,
              carrera_id: carreraId,
              origen_cohorte_id: cfg.origen_cohorte_id,
              destino_cohorte_id: cohorteDestinoId,
              desde: cfg.desde,
            }),
          )
        }
      }

      await Promise.all(jobs)
      setSuccessMsg('Cuatrimestre configurado exitosamente.')
      setStep(0)
      setState({ materias: [], cohortes: [], clonarConfig: {} })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al clonar equipos.'
      setErrorMsg(msg)
    } finally {
      setIsConfirming(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Asistente de Cuatrimestre</h2>
        <p className="text-sm text-gray-500">Configurá el nuevo cuatrimestre en 3 pasos</p>
      </div>

      {successMsg && (
        <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded px-3 py-2">
          {successMsg}
        </p>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <StepperCuatrimestre currentStep={step} />

        <div className="mt-8">
          {step === 0 && <PasoMateriasCohortesForm onNext={handlePaso1} />}
          {step === 1 && (
            <PasoEquiposForm
              cohortes={state.cohortes}
              onNext={handlePaso2}
              onBack={() => setStep(0)}
            />
          )}
          {step === 2 && (
            <ResumenCuatrimestre
              materias={state.materias}
              cohortes={state.cohortes}
              clonarConfig={state.clonarConfig}
              onConfirm={handleConfirm}
              onBack={() => setStep(1)}
              isConfirming={isConfirming}
              errorMsg={errorMsg}
            />
          )}
        </div>
      </div>
    </div>
  )
}
