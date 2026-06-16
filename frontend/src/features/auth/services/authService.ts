import { api } from '@/shared/services/api'
import type { LoginRequest, LoginOutcome, RefreshResponse } from '@/features/auth/types/auth.types'

export async function loginApi(req: LoginRequest): Promise<LoginOutcome> {
  const tenantId = import.meta.env.VITE_TENANT_ID as string | undefined
  const headers = tenantId ? { 'X-Tenant-Id': tenantId } : {}
  const { data } = await api.post<LoginOutcome>('/api/auth/login', req, { headers })
  return data
}

export async function refreshApi(refreshToken: string): Promise<RefreshResponse> {
  const { data } = await api.post<RefreshResponse>('/api/auth/refresh', {
    refresh_token: refreshToken,
  })
  return data
}

export async function verifyTwoFaApi(
  challengeToken: string,
  code: string,
): Promise<RefreshResponse> {
  const { data } = await api.post<RefreshResponse>('/api/auth/2fa/verify', {
    challenge_token: challengeToken,
    code,
  })
  return data
}
