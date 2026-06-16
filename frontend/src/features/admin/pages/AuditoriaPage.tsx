// features/admin/pages/AuditoriaPage.tsx
import { PanelAuditoria } from '../components/PanelAuditoria'
import { PageHelp } from '@/shared/components/PageHelp'
import { helpContent } from '@/shared/utils/helpContent'

export function AuditoriaPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Auditoría</h2>
        <PageHelp>{helpContent.auditoria}</PageHelp>
      </div>
      <PanelAuditoria />
    </div>
  )
}
