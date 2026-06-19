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
import {
  getMeApi,
  loginApi,
  refreshApi,
  verify2FAApi,
  enroll2FAApi,
  confirm2FAApi,
  forgotPasswordApi,
  resetPasswordApi,
  impersonateApi,
  endImpersonationApi,
} from '@/features/auth/services/authService'
import {
  isAuthChallenge,
  type AuthChallenge,
  type LoginRequest,
  type User,
  type TotpEnrollResponse,
  type TotpConfirmResponse,
  type ForgotResponse,
} from '@/features/auth/types/auth.types'

interface DecodedUser extends User {
  impersonating_user_id?: string
}

function decodeJwtUser(token: string): DecodedUser | null {
  try {
    const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(b64)) as Record<string, unknown>
    return {
      id: (payload.sub as string) ?? '',
      email: '',
      full_name: '',
      tenant_id: (payload.tenant_id as string) ?? '',
      roles: Array.isArray(payload.roles) ? (payload.roles as string[]) : [],
      impersonating_user_id: (payload.impersonating_user_id as string) ?? undefined,
    }
  } catch {
    return null
  }
}

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  challenge: AuthChallenge | null
  impersonatingUserId: string | null
  login: (req: LoginRequest) => Promise<void>
  logout: () => void
  verify2FA: (code: string) => Promise<void>
  enrollTOTP: () => Promise<TotpEnrollResponse>
  confirmTOTP: (code: string) => Promise<TotpConfirmResponse>
  forgotPassword: (email: string) => Promise<ForgotResponse>
  resetPassword: (token: string, new_password: string) => Promise<void>
  startImpersonation: (userId: string) => Promise<void>
  stopImpersonating: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [challenge, setChallenge] = useState<AuthChallenge | null>(null)
  const [impersonatingUserId, setImpersonatingUserId] = useState<string | null>(null)

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

        const decoded = decodeJwtUser(data.access_token)
        if (decoded?.impersonating_user_id) {
          setImpersonatingUserId(decoded.impersonating_user_id)
        }

        return getMeApi()
      })
      .then((me) => {
        setUser(me)
        setIsAuthenticated(true)
      })
      .catch(() => {
        localStorage.removeItem('rt')
        clearImpersonationState()
        setIsAuthenticated(false)
      })
      .finally(() => {
        setIsLoading(false)
      })
  }, [])

  function clearImpersonationState() {
    setImpersonatingUserId(null)
  }

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

  const verify2FA = useCallback(async (code: string): Promise<void> => {
    if (!challenge) throw new Error('No active 2FA challenge')

    const result = await verify2FAApi(challenge.challenge_token, code)

    setAccessToken(result.access_token)
    localStorage.setItem('rt', result.refresh_token)
    const me = await getMeApi()
    setUser(me)
    setIsAuthenticated(true)
    setChallenge(null)
  }, [challenge])

  const enrollTOTP = useCallback(async (): Promise<TotpEnrollResponse> => {
    return enroll2FAApi()
  }, [])

  const confirmTOTP = useCallback(
    async (code: string): Promise<TotpConfirmResponse> => {
      return confirm2FAApi({ code })
    },
    [],
  )

  const forgotPassword = useCallback(
    async (email: string): Promise<ForgotResponse> => {
      return forgotPasswordApi({ email })
    },
    [],
  )

  const resetPassword = useCallback(
    async (token: string, new_password: string): Promise<void> => {
      await resetPasswordApi({ token, new_password })
    },
    [],
  )

  const startImpersonation = useCallback(
    async (userId: string): Promise<void> => {
      const result = await impersonateApi({ user_id: userId })

      setAccessToken(result.access_token)
      setImpersonatingUserId(result.impersonating_user_id)

      const me = await getMeApi()
      setUser(me)
      setIsAuthenticated(true)
    },
    [],
  )

  const stopImpersonating = useCallback(async (): Promise<void> => {
    const result = await endImpersonationApi()

    setAccessToken(result.access_token)
    clearImpersonationState()

    const me = await getMeApi()
    setUser(me)
    setIsAuthenticated(true)
  }, [])

  const logout = useCallback((): void => {
    setUser(null)
    setIsAuthenticated(false)
    setChallenge(null)
    clearImpersonationState()
    clearSession()
  }, [])

  const value: AuthContextValue = {
    user,
    isAuthenticated,
    isLoading,
    challenge,
    impersonatingUserId,
    login,
    logout,
    verify2FA,
    enrollTOTP,
    confirmTOTP,
    forgotPassword,
    resetPassword,
    startImpersonation,
    stopImpersonating,
  }

  return createElement(AuthContext.Provider, { value }, children)
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within <AuthProvider>')
  }
  return ctx
}

export { AuthContext }
