// features/comision/pages/MonitorPage.tsx
// Monitor with filters and paginated table.
import { useState } from 'react'
import { FiltrosMonitor } from '../components/FiltrosMonitor'
import { TablaMonitor } from '../components/TablaMonitor'
import type { MonitorParams } from '../types'

export function MonitorPage() {
  const [params, setParams] = useState<MonitorParams>({ limit: 100, offset: 0 })

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Monitor de seguimiento</h2>
      <FiltrosMonitor onBuscar={setParams} />
      <TablaMonitor params={params} />
    </div>
  )
}
