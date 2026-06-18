import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  createElement,
  type ReactNode,
} from 'react'
import { setAccessToken, clearSession } from '@/shared/services/api'
import { getMeApi, loginApi, refreshApi } from '@/features/auth/services/authService'
import {
  isAuthChallenge,
  type AuthChallenge,
  type LoginRequest,
  type User,
} from '@/features/auth/types/auth.types'

// Decode JWT payload without verifying signature (backend already verified it).
// Used to extract sub, tenant_id and roles for the UI.
function decodeJwtUser(token: string): User | null {
  try {
    const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(b64)) as Record<string, unknown>
    return {
      id: (payload.sub as string) ?? '',
      email: '',
      full_name: '',
      tenant_id: (payload.tenant_id as string) ?? '',
      roles: Array.isArray(payload.roles) ? (payload.roles as string[]) : [],
    }
  } catch {
    return null
  }
}

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------
interface AuthContextValue {
  user: User | null
  /** True when an access token has been obtained (login or silent refresh) */
  isAuthenticated: boolean
  /** True while the initial silent-refresh attempt is in progress */
  isLoading: boolean
  /** Set when backend requires 2FA — contains the challenge_token */
  challenge: AuthChallenge | null
  login: (req: LoginRequest) => Promise<void>
  logout: () => void
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
const AuthContext = createContext<AuthContextValue | null>(null)

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------
interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [challenge, setChallenge] = useState<AuthChallenge | null>(null)

  // On mount: attempt silent refresh to restore session across reloads
  useEffect(() => {
    const rt = localStorage.getItem('rt')
    if (!rt) {
      setIsLoading(false)
      return
    }

    refreshApi(rt)
      .then((data) => {
        setAccessToken(data.access_token)
        localStorage.setItem('rt', data.refresh_token)
        return getMeApi()
      })
      .then((me) => {
        setUser(me)
        setIsAuthenticated(true)
      })
      .catch(() => {
        localStorage.removeItem('rt')
        setIsAuthenticated(false)
      })
      .finally(() => {
        setIsLoading(false)
      })
  }, [])

  const login = useCallback(async (req: LoginRequest): Promise<void> => {
    const outcome = await loginApi(req)

    if (isAuthChallenge(outcome)) {
      setChallenge(outcome)
      return
    }

    setAccessToken(outcome.access_token)
    localStorage.setItem('rt', outcome.refresh_token)
    const me = await getMeApi()
    setUser(me)
    setIsAuthenticated(true)
    setChallenge(null)
  }, [])

  const logout = useCallback((): void => {
    setUser(null)
    setIsAuthenticated(false)
    setChallenge(null)
    clearSession()
  }, [])

  const value: AuthContextValue = {
    user,
    isAuthenticated,
    isLoading,
    challenge,
    login,
    logout,
  }

  return createElement(AuthContext.Provider, { value }, children)
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within <AuthProvider>')
  }
  return ctx
}

export { AuthContext }
