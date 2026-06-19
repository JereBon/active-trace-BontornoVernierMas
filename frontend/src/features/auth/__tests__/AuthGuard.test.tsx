import type { ReactNode } from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthGuard } from '../components/AuthGuard'
import { AuthContext } from '../hooks/useAuth'
import type { User } from '../types'

function makeWrapper(user: User | null, isLoading = false) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/protected']}>
          <AuthContext.Provider
            value={{
              user,
              isAuthenticated: user !== null,
              isLoading,
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

  return Wrapper
}

describe('AuthGuard', () => {
  it('renders children when authenticated', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['PROFESOR'] }
    const Wrapper = makeWrapper(user)

    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
      { wrapper: Wrapper },
    )

    expect(screen.getByText('Protected content')).toBeTruthy()
  })

  it('redirects to login when not authenticated', () => {
    const Wrapper = makeWrapper(null)

    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
      { wrapper: Wrapper },
    )

    expect(screen.queryByText('Protected content')).toBeNull()
  })

  it('redirects to dashboard when user lacks required role', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['PROFESOR'] }
    const Wrapper = makeWrapper(user)

    render(
      <AuthGuard requiredRoles={['ADMIN']}>
        <div>Admin only</div>
      </AuthGuard>,
      { wrapper: Wrapper },
    )

    expect(screen.queryByText('Admin only')).toBeNull()
  })

  it('renders children when user has required role', () => {
    const user: User = { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['ADMIN'] }
    const Wrapper = makeWrapper(user)

    render(
      <AuthGuard requiredRoles={['ADMIN']}>
        <div>Admin only</div>
      </AuthGuard>,
      { wrapper: Wrapper },
    )

    expect(screen.getByText('Admin only')).toBeTruthy()
  })

  it('shows spinner while loading', () => {
    const Wrapper = makeWrapper(null, true)

    render(
      <AuthGuard>
        <div>Content</div>
      </AuthGuard>,
      { wrapper: Wrapper },
    )

    expect(screen.getByRole('status')).toBeTruthy()
  })
})
