export interface User {
  id: string
  email: string
  full_name: string
  tenant_id: string
  roles: string[]
  totp_activo: boolean
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuthChallenge {
  challenge: '2fa_required'
  challenge_token: string
}

export type LoginOutcome = LoginResponse | AuthChallenge

export function isAuthChallenge(outcome: LoginOutcome): outcome is AuthChallenge {
  return (outcome as AuthChallenge).challenge === '2fa_required'
}

export interface TwoFAVerifyRequest {
  challenge_token: string
  code: string
}

export interface SessionResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface TotpEnrollResponse {
  secret: string
  uri: string
}

export interface TotpConfirmRequest {
  code: string
}

export interface TotpConfirmResponse {
  activated: boolean
}

export interface ForgotRequest {
  email: string
  dev_mode?: boolean
}

export interface ForgotResponse {
  message: string
  token?: string | null
}

export interface ResetRequest {
  token: string
  new_password: string
}

export interface ImpersonateRequest {
  user_id: string
}

export interface ImpersonateResponse {
  access_token: string
  token_type: string
  impersonating_user_id: string
}
