import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useUsuarios } from '@/features/admin/hooks/useUsuarios'
import { useMaterias, useCohortes } from '@/features/admin/hooks/useEstructura'
import { getAvisos } from '@/features/coordinacion/services/avisosService'
import { getMisTareas } from '@/features/coordinacion/services/tareasService'
import { PageHelp } from '@/shared/components/PageHelp'
import { helpContent } from '@/shared/utils/helpContent'

function StatCard({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-5 flex flex-col gap-1 ${color}`}>
      <span className="text-3xl font-bold text-gray-900">{value}</span>
      <span className="text-sm text-gray-500">{label}</span>
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="text-base font-semibold text-gray-700 mb-3">{children}</h2>
}

export function DashboardPage() {
  const { user } = useAuth()
  const { data: usuarios = [] } = useUsuarios()
  const { data: materias = [] } = useMaterias()
  const { data: cohortes = [] } = useCohortes()
  const { data: avisos = [] } = useQuery({
    queryKey: ['avisos-consumer'],
    queryFn: getAvisos,
  })
  const { data: misTareas = [] } = useQuery({
    queryKey: ['mis-tareas-dashboard'],
    queryFn: getMisTareas,
  })

  const currentUser = usuarios.find((u) => u.id === user?.id)
  const displayName = currentUser
    ? `${currentUser.nombre} ${currentUser.apellidos}`
    : (user?.roles ?? []).join(', ') || 'Usuario'

  const tareasPendientes = misTareas.filter(
    (t) => t.estado === 'Pendiente' || t.estado === 'En_progreso',
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Bienvenido, {displayName}</h1>
          {user?.roles && user.roles.length > 0 && (
            <p className="text-sm text-gray-400 mt-0.5">
              {user.roles.join(' · ')}
            </p>
          )}
        </div>
        <PageHelp>{helpContent.dashboard}</PageHelp>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Materias" value={materias.length} color="" />
        <StatCard label="Cohortes" value={cohortes.length} color="" />
        <StatCard label="Usuarios" value={usuarios.length} color="" />
        <StatCard label="Avisos vigentes" value={avisos.length} color="" />
      </div>

      {/* Acceso rápido por materia */}
      {materias.length > 0 && (
        <div>
          <SectionTitle>Módulo comisión por materia</SectionTitle>
          <div className="flex flex-wrap gap-3">
            {materias.map((m) => (
              <Link
                key={m.id}
                to={`/comision/${m.id}/atrasados`}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:border-blue-400 hover:text-blue-700 transition-colors"
              >
                {m.nombre}
                <span className="text-gray-400 text-xs">({m.codigo})</span>
                <span className="text-gray-300">→</span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Quick links */}
      <div>
        <SectionTitle>Accesos rápidos</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Link
            to="/coordinacion/equipos"
            className="flex flex-col gap-1 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-400 hover:shadow-sm transition-all"
          >
            <span className="font-medium text-gray-800 text-sm">Coordinación</span>
            <span className="text-xs text-gray-400">Equipos · Avisos · Tareas</span>
          </Link>
          <Link
            to="/admin/estructura"
            className="flex flex-col gap-1 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-400 hover:shadow-sm transition-all"
          >
            <span className="font-medium text-gray-800 text-sm">Administración</span>
            <span className="text-xs text-gray-400">Usuarios · Estructura</span>
          </Link>
          <Link
            to="/finanzas/periodo"
            className="flex flex-col gap-1 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-400 hover:shadow-sm transition-all"
          >
            <span className="font-medium text-gray-800 text-sm">Finanzas</span>
            <span className="text-xs text-gray-400">Liquidaciones · Grilla</span>
          </Link>
          <Link
            to="/coordinacion/monitor"
            className="flex flex-col gap-1 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-400 hover:shadow-sm transition-all"
          >
            <span className="font-medium text-gray-800 text-sm">Monitor Global</span>
            <span className="text-xs text-gray-400">Seguimiento general</span>
          </Link>
        </div>
      </div>

      {/* Bottom two columns: Avisos + Tareas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Avisos vigentes */}
        <div>
          <SectionTitle>Avisos vigentes</SectionTitle>
          <div className="bg-white border border-gray-200 rounded-lg divide-y divide-gray-100">
            {avisos.length === 0 ? (
              <p className="text-center text-gray-400 text-sm py-6">Sin avisos activos.</p>
            ) : (
              avisos.slice(0, 5).map((a) => (
                <div key={a.id} className="px-4 py-3">
                  <p className="text-sm font-medium text-gray-900">{a.titulo}</p>
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{a.cuerpo}</p>
                  <p className="text-xs text-gray-300 mt-1">
                    Hasta {new Date(a.vig_hasta.slice(0, 10) + 'T12:00:00').toLocaleDateString('es-AR')}
                  </p>
                </div>
              ))
            )}
            {avisos.length > 5 && (
              <div className="px-4 py-2">
                <span className="text-xs text-gray-400">{avisos.length - 5} avisos más</span>
              </div>
            )}
          </div>
        </div>

        {/* Mis tareas activas */}
        <div>
          <SectionTitle>
            Mis tareas activas
            {tareasPendientes.length > 0 && (
              <span className="ml-2 px-1.5 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded-full">
                {tareasPendientes.length}
              </span>
            )}
          </SectionTitle>
          <div className="bg-white border border-gray-200 rounded-lg divide-y divide-gray-100">
            {tareasPendientes.length === 0 ? (
              <p className="text-center text-gray-400 text-sm py-6">Sin tareas pendientes.</p>
            ) : (
              tareasPendientes.slice(0, 5).map((t) => (
                <div key={t.id} className="px-4 py-3 flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t.titulo}</p>
                    {t.descripcion && (
                      <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{t.descripcion}</p>
                    )}
                  </div>
                  <span
                    className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${
                      t.estado === 'En_progreso'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}
                  >
                    {t.estado.replace('_', ' ')}
                  </span>
                </div>
              ))
            )}
            {tareasPendientes.length > 5 && (
              <div className="px-4 py-2">
                <Link to="/coordinacion/tareas" className="text-xs text-blue-600 hover:underline">
                  Ver todas ({tareasPendientes.length})
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
