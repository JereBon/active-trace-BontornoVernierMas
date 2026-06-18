import { useState } from 'react'
import { StepperCuatrimestre } from '../components/cuatrimestre/StepperCuatrimestre'
import { PasoMateriasCohortesForm } from '../components/cuatrimestre/PasoMateriasCohortesForm'
import { PasoEquiposForm } from '../components/cuatrimestre/PasoEquiposForm'
import { ResumenCuatrimestre } from '../components/cuatrimestre/ResumenCuatrimestre'
import { useConfirmarCuatrimestre } from '../hooks/useCuatrimestre'
import type { Materia, Cohorte } from '../../admin/types'
import type { AsignacionCuatrimestre } from '../types'

export function CuatrimestrePage() {
  const [step, setStep] = useState(0)
  const [materias, setMaterias] = useState<Materia[]>([])
  const [cohortes, setCohortes] = useState<Cohorte[]>([])
  const [asignaciones, setAsignaciones] = useState<AsignacionCuatrimestre[]>([])
  const [mensaje, setMensaje] = useState<string | null>(null)

  const confirmarMutation = useConfirmarCuatrimestre()

  const handlePaso1 = (data: { materias: Materia[]; cohortes: Cohorte[] }) => {
    setMaterias(data.materias)
    setCohortes(data.cohortes)
    setStep(1)
  }

  const handlePaso2 = (asignaciones: AsignacionCuatrimestre[]) => {
    setAsignaciones(asignaciones)
    setStep(2)
  }

  const handleConfirm = async () => {
    setMensaje(null)
    try {
      await confirmarMutation.mutateAsync(asignaciones)
      setMensaje('Cuatrimestre configurado exitosamente')
      setStep(0)
      setMaterias([])
      setCohortes([])
      setAsignaciones([])
    } catch {
      setMensaje('Error al configurar el cuatrimestre')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">
          Asistente de Cuatrimestre
        </h2>
        <p className="text-sm text-gray-500">
          Configurá el nuevo cuatrimestre en 3 pasos
        </p>
      </div>

      {mensaje && (
        <div
          className={`px-4 py-2 rounded text-sm ${
            mensaje.includes('Error')
              ? 'bg-red-50 text-red-700 border border-red-200'
              : 'bg-green-50 text-green-700 border border-green-200'
          }`}
        >
          {mensaje}
        </div>
      )}

      {confirmarMutation.isPending && (
        <div className="px-4 py-2 rounded text-sm bg-blue-50 text-blue-700 border border-blue-200">
          Configurando cuatrimestre...
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <StepperCuatrimestre currentStep={step} />

        <div className="mt-8">
          {step === 0 && (
            <PasoMateriasCohortesForm onNext={handlePaso1} />
          )}
          {step === 1 && (
            <PasoEquiposForm
              materias={materias}
              onNext={handlePaso2}
              onBack={() => setStep(0)}
            />
          )}
          {step === 2 && (
            <ResumenCuatrimestre
              materias={materias}
              cohortes={cohortes}
              asignaciones={asignaciones}
              onConfirm={handleConfirm}
              onBack={() => setStep(1)}
              isConfirming={confirmarMutation.isPending}
            />
          )}
        </div>
      </div>
    </div>
  )
}
