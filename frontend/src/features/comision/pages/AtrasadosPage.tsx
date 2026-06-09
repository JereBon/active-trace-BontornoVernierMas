// features/comision/pages/AtrasadosPage.tsx
// Tabs: Atrasados | Ranking | Notas Finales | Reporte
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { TablaAtrasados } from '../components/TablaAtrasados'
import { TablaRanking } from '../components/TablaRanking'
import { TablaNotasFinales } from '../components/TablaNotasFinales'
import { ReporteMateriaCards } from '../components/ReporteMateriaCards'

type TabId = 'atrasados' | 'ranking' | 'notas' | 'reporte'

const TABS: { id: TabId; label: string }[] = [
  { id: 'atrasados', label: 'Atrasados' },
  { id: 'ranking', label: 'Ranking' },
  { id: 'notas', label: 'Notas Finales' },
  { id: 'reporte', label: 'Reporte' },
]

export function AtrasadosPage() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const [activeTab, setActiveTab] = useState<TabId>('atrasados')

  if (!materiaId) return null

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Análisis académico</h2>

      {/* Tab bar */}
      <div className="flex border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={[
              'px-4 py-2 text-sm font-medium transition-colors',
              activeTab === tab.id
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700',
            ].join(' ')}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'atrasados' && <TablaAtrasados materiaId={materiaId} />}
        {activeTab === 'ranking' && <TablaRanking materiaId={materiaId} />}
        {activeTab === 'notas' && <TablaNotasFinales materiaId={materiaId} />}
        {activeTab === 'reporte' && <ReporteMateriaCards materiaId={materiaId} />}
      </div>
    </div>
  )
}
