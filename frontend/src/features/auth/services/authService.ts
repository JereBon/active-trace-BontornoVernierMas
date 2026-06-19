import { api } from '@/shared/services/api'
import type {
  LoginRequest,
  LoginOutcome,
  RefreshResponse,
  SessionResponse,
  TotpEnrollResponse,
  TotpConfirmRequest,
  TotpConfirmResponse,
  ForgotRequest,
  ForgotResponse,
  ResetRequest,
  ImpersonateRequest,
  ImpersonateResponse,
  User,
} from '@/features/auth/types/auth.types'

export async function loginApi(req: LoginRequest): Promise<LoginOutcome> {
  const { data } = await api.post<LoginOutcome>('/api/auth/login', req)
  return data
}

export async function refreshApi(refreshToken: string): Promise<RefreshResponse> {
  const { data } = await api.post<RefreshResponse>('/api/auth/refresh', {
    refresh_token: refreshToken,
  })
  return data
}

export async function getMeApi(): Promise<User> {
  const { data } = await api.get<User>('/api/auth/me')
  return data
}

export async function verify2FAApi(
  challenge_token: string,
  code: string,
): Promise<SessionResponse> {
  const { data } = await api.post<SessionResponse>('/api/auth/2fa/verify', {
    challenge_token,
    code,
  })
  return data
}

export async function enroll2FAApi(): Promise<TotpEnrollResponse> {
  const { data } = await api.post<TotpEnrollResponse>('/api/auth/2fa/enroll')
  return data
}

export async function confirm2FAApi(
  req: TotpConfirmRequest,
): Promise<TotpConfirmResponse> {
  const { data } = await api.post<TotpConfirmResponse>(
    '/api/auth/2fa/confirm',
    req,
  )
  return data
}

export async function forgotPasswordApi(
  req: ForgotRequest,
): Promise<ForgotResponse> {
  const { data } = await api.post<ForgotResponse>('/api/auth/forgot', {
    ...req,
    dev_mode: true,
  })
  return data
}

export async function resetPasswordApi(req: ResetRequest): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/api/auth/reset', req)
  return data
}

export async function impersonateApi(
  req: ImpersonateRequest,
): Promise<ImpersonateResponse> {
  const { data } = await api.post<ImpersonateResponse>(
    '/api/auth/impersonate',
    req,
  )
  return data
}

export async function endImpersonationApi(): Promise<SessionResponse> {
  const { data } = await api.post<SessionResponse>(
    '/api/auth/impersonate/end',
  )
  return data
}
