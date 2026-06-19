import type { ReactNode } from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardPage } from '../pages/DashboardPage'
import { AuthContext } from '@/features/auth/hooks/useAuth'
import type { User } from '@/features/auth/types/auth.types'

function renderDashboard(user: User | null) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <AuthContext.Provider
            value={{
              user,
              isAuthenticated: user !== null,
              isLoading: false,
              challenge: null,
              impersonatingUserId: null,
              login: vi.fn(),
              logout: vi.fn(),
              verify2FA: vi.fn(),
              enrollTOTP: vi.fn().mockResolvedValue({ secret: '', uri: '' }),
              confirmTOTP: vi.fn().mockResolvedValue({ activated: false }),
              forgotPassword: vi.fn(),
              resetPassword: vi.fn(),
              startImpersonation: vi.fn(),
              stopImpersonating: vi.fn(),
            }}
          >
            {children}
          </AuthContext.Provider>
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  return render(<DashboardPage />, { wrapper: Wrapper })
}

describe('DashboardPage', () => {
  it('shows welcome message with user name', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Carlos Pérez', tenant_id: 't1', roles: ['PROFESOR'] }
    renderDashboard(user)
    expect(screen.getByText(/Bienvenido/)).toBeTruthy()
    expect(screen.getByText(/Carlos Pérez/)).toBeTruthy()
  })

  it('shows Comision card for PROFESOR', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['PROFESOR'] }
    renderDashboard(user)
    expect(screen.getByText('Comisión')).toBeTruthy()
  })

  it('shows Coordinacion card for COORDINADOR', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['COORDINADOR'] }
    renderDashboard(user)
    expect(screen.getByText('Coordinación')).toBeTruthy()
  })

  it('shows Finanzas card for FINANZAS', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['FINANZAS'] }
    renderDashboard(user)
    expect(screen.getByText('Finanzas')).toBeTruthy()
  })

  it('shows Admin card for ADMIN', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['ADMIN'] }
    renderDashboard(user)
    expect(screen.getByText('Administración')).toBeTruthy()
  })

  it('shows multiple cards when user has multiple roles', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['ADMIN', 'COORDINADOR'] }
    renderDashboard(user)
    expect(screen.getByText('Coordinación')).toBeTruthy()
    expect(screen.getByText('Administración')).toBeTruthy()
  })

  it('shows empty message when user has no matching cards', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['ALUMNO'] }
    renderDashboard(user)
    expect(screen.getByText(/No tenés módulos asignados/)).toBeTruthy()
  })
})
