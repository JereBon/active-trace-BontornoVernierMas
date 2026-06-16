export interface User {
  id: string
  email: string
  full_name: string
  tenant_id: string
  roles: string[]
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

/** Returned by the backend when 2FA is required */
export interface AuthChallenge {
  challenge: '2fa_required'
  challenge_token: string
}

/** Union of possible login outcomes */
export type LoginOutcome = LoginResponse | AuthChallenge

export function isAuthChallenge(outcome: LoginOutcome): outcome is AuthChallenge {
  return (outcome as AuthChallenge).challenge === '2fa_required'
}
