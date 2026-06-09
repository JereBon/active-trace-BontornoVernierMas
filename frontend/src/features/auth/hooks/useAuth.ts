import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  createElement,
  type ReactNode,
} from 'react'
import { setAccessToken, clearSession } from '@/shared/services/api'
import { queryClient } from '@/shared/queryClient'
import { loginApi, refreshApi } from '@/features/auth/services/authService'
import {
  isAuthChallenge,
  type AuthChallenge,
  type LoginRequest,
  type User,
} from '@/features/auth/types/auth.types'

function decodeUserFromToken(token: string): User | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return {
      id: payload.sub ?? '',
      email: '',
      full_name: '',
      tenant_id: payload.tenant_id ?? '',
      roles: payload.roles ?? [],
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
  // Guard against React 18 StrictMode double-firing this effect with the same token.
  const refreshFiredRef = useRef(false)

  // On mount: attempt silent refresh to restore session across reloads
  useEffect(() => {
    if (refreshFiredRef.current) return
    refreshFiredRef.current = true

    const rt = localStorage.getItem('rt')
    if (!rt) {
      setIsLoading(false)
      return
    }

    refreshApi(rt)
      .then((data) => {
        setAccessToken(data.access_token)
        localStorage.setItem('rt', data.refresh_token)
        setIsAuthenticated(true)
        const u = decodeUserFromToken(data.access_token)
        if (u) setUser(u)
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
    setUser(outcome.user ?? decodeUserFromToken(outcome.access_token))
    setIsAuthenticated(true)
    setChallenge(null)
  }, [])

  const logout = useCallback((): void => {
    setUser(null)
    setIsAuthenticated(false)
    setChallenge(null)
    clearSession()
    queryClient.clear()
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
