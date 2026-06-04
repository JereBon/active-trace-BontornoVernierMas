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
import { loginApi, refreshApi } from '@/features/auth/services/authService'
import {
  isAuthChallenge,
  type AuthChallenge,
  type LoginRequest,
  type User,
} from '@/features/auth/types/auth.types'

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
        setIsAuthenticated(true)
        // user details require a GET /api/auth/me call — added in a future change
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
    setUser(outcome.user)
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
