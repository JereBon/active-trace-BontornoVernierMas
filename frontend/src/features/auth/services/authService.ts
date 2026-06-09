import { api } from '@/shared/services/api'
import type { LoginRequest, LoginOutcome, RefreshResponse } from '@/features/auth/types/auth.types'

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
