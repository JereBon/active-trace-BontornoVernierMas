// features/admin/pages/UsuariosPage.tsx
import { TablaUsuarios } from '../components/TablaUsuarios'
import { PageHelp } from '@/shared/components/PageHelp'
import { helpContent } from '@/shared/utils/helpContent'

export function UsuariosPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">Usuarios</h2>
        <PageHelp>{helpContent.usuarios}</PageHelp>
      </div>
      <TablaUsuarios />
    </div>
  )
}
