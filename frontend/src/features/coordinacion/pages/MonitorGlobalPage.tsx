// features/coordinacion/pages/MonitorGlobalPage.tsx
import { MonitorGlobalPanel } from '../components/monitor/MonitorGlobalPanel'

export function MonitorGlobalPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Monitor Global</h2>
        <p className="text-sm text-gray-500">Vista transversal de todos los alumnos del tenant</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <MonitorGlobalPanel />
      </div>
    </div>
  )
}
