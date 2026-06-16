// features/coordinacion/components/cuatrimestre/StepperCuatrimestre.tsx
interface Step {
  label: string
  description: string
}

const STEPS: Step[] = [
  { label: 'Materias y Cohortes', description: 'Seleccioná las materias y cohortes del cuatrimestre' },
  { label: 'Equipos', description: 'Asigná equipos docentes por materia' },
  { label: 'Confirmación', description: 'Revisá y confirmá la configuración' },
]

interface Props {
  currentStep: number
}

export function StepperCuatrimestre({ currentStep }: Props) {
  return (
    <ol className="flex items-center w-full">
      {STEPS.map((step, idx) => {
        const isCompleted = idx < currentStep
        const isActive = idx === currentStep
        return (
          <li
            key={step.label}
            className={`flex items-center ${idx < STEPS.length - 1 ? 'flex-1' : ''}`}
          >
            <div className="flex flex-col items-center">
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium border-2 ${
                  isCompleted
                    ? 'border-blue-600 bg-blue-600 text-white'
                    : isActive
                    ? 'border-blue-600 bg-white text-blue-600'
                    : 'border-gray-300 bg-white text-gray-400'
                }`}
              >
                {isCompleted ? '✓' : idx + 1}
              </span>
              <span
                className={`mt-2 text-xs font-medium ${
                  isActive ? 'text-blue-600' : isCompleted ? 'text-gray-700' : 'text-gray-400'
                }`}
              >
                {step.label}
              </span>
              <span className="text-xs text-gray-400 max-w-24 text-center hidden sm:block">
                {step.description}
              </span>
            </div>
            {idx < STEPS.length - 1 && (
              <div
                className={`flex-1 h-0.5 mx-2 mb-6 ${isCompleted ? 'bg-blue-600' : 'bg-gray-200'}`}
              />
            )}
          </li>
        )
      })}
    </ol>
  )
}
