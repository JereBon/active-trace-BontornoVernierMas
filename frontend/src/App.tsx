import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/features/auth/hooks/useAuth'
import { AuthGuard } from '@/features/auth/components/AuthGuard'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { ForgotPasswordPage } from '@/features/auth/pages/ForgotPasswordPage'
import { ResetPasswordPage } from '@/features/auth/pages/ResetPasswordPage'
import { PerfilPage } from '@/features/auth/pages/PerfilPage'
import { TwoFactorEnrollPage } from '@/features/auth/pages/TwoFactorEnrollPage'
import { InboxPage } from '@/features/inbox/pages/InboxPage'
import { AppShell } from '@/shared/components/AppShell'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { ComisionLayout } from '@/features/comision/pages/ComisionLayout'
import { ComisionIndexPage } from '@/features/comision/pages/ComisionIndexPage'
import { ImportacionPage } from '@/features/comision/pages/ImportacionPage'
import { PadronPage } from '@/features/comision/pages/PadronPage'
import { AtrasadosPage } from '@/features/comision/pages/AtrasadosPage'
import { SinCorregirPage } from '@/features/comision/pages/SinCorregirPage'
import { ComunicacionPage } from '@/features/comision/pages/ComunicacionPage'
import { MonitorPage } from '@/features/comision/pages/MonitorPage'
import { CoordinacionLayout } from '@/features/coordinacion/pages/CoordinacionLayout'
import { EquiposPage } from '@/features/coordinacion/pages/EquiposPage'
import { AvisosPage } from '@/features/coordinacion/pages/AvisosPage'
import { TareasPage } from '@/features/coordinacion/pages/TareasPage'
import { MonitorGlobalPage } from '@/features/coordinacion/pages/MonitorGlobalPage'
import { EncuentrosPage } from '@/features/coordinacion/pages/EncuentrosPage'
import { ColoquiosPage } from '@/features/coordinacion/pages/ColoquiosPage'
import { CuatrimestrePage } from '@/features/coordinacion/pages/CuatrimestrePage'
import { GuardiasPage } from '@/features/coordinacion/pages/GuardiasPage'
import { AprobacionesPage } from '@/features/coordinacion/pages/AprobacionesPage'
import { ProgramasPage } from '@/features/coordinacion/pages/ProgramasPage'
import { FechasPage } from '@/features/coordinacion/pages/FechasPage'
import { FinanzasLayout } from '@/features/finanzas/pages/FinanzasLayout'
import { PeriodoPage } from '@/features/finanzas/pages/PeriodoPage'
import { HistorialPage } from '@/features/finanzas/pages/HistorialPage'
import { GrillaPage } from '@/features/finanzas/pages/GrillaPage'
import { FacturasPage } from '@/features/finanzas/pages/FacturasPage'
import { AdminLayout } from '@/features/admin/pages/AdminLayout'
import { EstructuraPage } from '@/features/admin/pages/EstructuraPage'
import { UsuariosPage } from '@/features/admin/pages/UsuariosPage'
import { AuditoriaPage } from '@/features/admin/pages/AuditoriaPage'
import { ColoquiosAlumnoPage } from '@/features/alumno/pages/ColoquiosAlumnoPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            {/* Protected routes — AuthGuard + AppShell */}
            <Route element={<AuthGuard><AppShell /></AuthGuard>}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/perfil" element={<PerfilPage />} />
              <Route path="/perfil/2fa" element={<TwoFactorEnrollPage />} />
              <Route path="/inbox" element={<InboxPage />} />

              {/* Comision — PROFESOR/TUTOR/COORDINADOR/ADMIN */}
              <Route path="/comision" element={<AuthGuard requiredRoles={['PROFESOR', 'TUTOR', 'COORDINADOR', 'ADMIN']}><ComisionIndexPage /></AuthGuard>} />
              <Route path="/comision/:materiaId" element={<AuthGuard requiredRoles={['PROFESOR', 'TUTOR', 'COORDINADOR', 'ADMIN']}><ComisionLayout /></AuthGuard>}>
                <Route index element={<Navigate to="atrasados" replace />} />
                <Route path="padron" element={<PadronPage />} />
                <Route path="importacion" element={<ImportacionPage />} />
                <Route path="atrasados" element={<AtrasadosPage />} />
                <Route path="sin-corregir" element={<SinCorregirPage />} />
                <Route path="comunicacion" element={<ComunicacionPage />} />
                <Route path="monitor" element={<MonitorPage />} />
              </Route>

              {/* Coordinacion — COORDINADOR/ADMIN */}
              <Route path="/coordinacion" element={<AuthGuard requiredRoles={['COORDINADOR', 'ADMIN']}><CoordinacionLayout /></AuthGuard>}>
                <Route index element={<Navigate to="equipos" replace />} />
                <Route path="equipos" element={<EquiposPage />} />
                <Route path="avisos" element={<AvisosPage />} />
              <Route path="tareas" element={<TareasPage />} />
              <Route path="programas" element={<ProgramasPage />} />
              <Route path="fechas" element={<FechasPage />} />
              <Route path="monitor" element={<MonitorGlobalPage />} />
                <Route path="encuentros" element={<EncuentrosPage />} />
                <Route path="coloquios" element={<ColoquiosPage />} />
                <Route path="cuatrimestre" element={<CuatrimestrePage />} />
                <Route path="guardias" element={<GuardiasPage />} />
                <Route path="aprobaciones" element={<AprobacionesPage />} />
              </Route>

              {/* Finanzas — FINANZAS/ADMIN */}
              <Route path="/finanzas" element={<AuthGuard requiredRoles={['FINANZAS', 'ADMIN']}><FinanzasLayout /></AuthGuard>}>
                <Route index element={<Navigate to="periodo" replace />} />
                <Route path="periodo" element={<PeriodoPage />} />
                <Route path="historial" element={<HistorialPage />} />
                <Route path="grilla" element={<GrillaPage />} />
                <Route path="facturas" element={<FacturasPage />} />
              </Route>

              {/* Admin — ADMIN */}
              <Route path="/admin" element={<AuthGuard requiredRoles={['ADMIN']}><AdminLayout /></AuthGuard>}>
                <Route index element={<Navigate to="estructura" replace />} />
                <Route path="estructura" element={<EstructuraPage />} />
                <Route path="usuarios" element={<UsuariosPage />} />
                <Route path="auditoria" element={<AuditoriaPage />} />
              </Route>

              {/* Alumno — ALUMNO */}
              <Route path="/alumno/coloquios" element={<AuthGuard requiredRoles={['ALUMNO']}><ColoquiosAlumnoPage /></AuthGuard>} />

              {/* Redirect root to dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
