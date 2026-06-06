// features/coordinacion/pages/CuatrimestrePage.tsx
import { useState } from 'react'
import { StepperCuatrimestre } from '../components/cuatrimestre/StepperCuatrimestre'
import { PasoMateriasCohortesForm } from '../components/cuatrimestre/PasoMateriasCohortesForm'
import { PasoEquiposForm } from '../components/cuatrimestre/PasoEquiposForm'
import { ResumenCuatrimestre } from '../components/cuatrimestre/ResumenCuatrimestre'

interface CuatrimestreState {
  materias: string[]
  cohortes: string[]
  asignaciones: Record<string, string>
}

export function CuatrimestrePage() {
  const [step, setStep] = useState(0)
  const [isConfirming, setIsConfirming] = useState(false)
  const [state, setState] = useState<CuatrimestreState>({
    materias: [],
    cohortes: [],
    asignaciones: {},
  })

  const handlePaso1 = (data: { materias: string[]; cohortes: string[] }) => {
    setState((prev) => ({ ...prev, ...data }))
    setStep(1)
  }

  const handlePaso2 = (asignaciones: Record<string, string>) => {
    setState((prev) => ({ ...prev, asignaciones }))
    setStep(2)
  }

  const handleConfirm = () => {
    setIsConfirming(true)
    // In a real scenario this would call an API endpoint.
    // For now, simulate success and reset the stepper.
    setTimeout(() => {
      setIsConfirming(false)
      setStep(0)
      setState({ materias: [], cohortes: [], asignaciones: {} })
    }, 1500)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Asistente de Cuatrimestre</h2>
        <p className="text-sm text-gray-500">Configurá el nuevo cuatrimestre en 3 pasos</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <StepperCuatrimestre currentStep={step} />

        <div className="mt-8">
          {step === 0 && <PasoMateriasCohortesForm onNext={handlePaso1} />}
          {step === 1 && (
            <PasoEquiposForm
              materias={state.materias}
              onNext={handlePaso2}
              onBack={() => setStep(0)}
            />
          )}
          {step === 2 && (
            <ResumenCuatrimestre
              materias={state.materias}
              cohortes={state.cohortes}
              asignaciones={state.asignaciones}
              onConfirm={handleConfirm}
              onBack={() => setStep(1)}
              isConfirming={isConfirming}
            />
          )}
        </div>
      </div>
    </div>
  )
}
