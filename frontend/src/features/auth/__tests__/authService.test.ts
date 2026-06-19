import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from '@/shared/services/api'

vi.mock('@/shared/services/api', () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

const mockPost = api.post as ReturnType<typeof vi.fn>
const mockGet = api.get as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

describe('authService', () => {
  it('loginApi sends email and password', async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: 'tok', refresh_token: 'rt', token_type: 'bearer', user: { id: '1', email: 'a@b.com', full_name: 'Test', tenant_id: 't1', roles: ['PROFESOR'] } },
    })

    const { loginApi } = await import('../services/authService')
    const result = await loginApi({ email: 'a@b.com', password: 'pass' })

    expect(mockPost).toHaveBeenCalledWith('/api/auth/login', {
      email: 'a@b.com',
      password: 'pass',
    })
    expect(result).toHaveProperty('access_token')
  })

  it('loginApi returns AuthChallenge when 2FA required', async () => {
    const challenge = { challenge: '2fa_required' as const, challenge_token: 'ct' }
    mockPost.mockResolvedValueOnce({ data: challenge })

    const { loginApi } = await import('../services/authService')
    const result = await loginApi({ email: 'a@b.com', password: 'pass' })

    expect(result).toEqual(challenge)
  })

  it('verify2FAApi sends challenge_token and code', async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: 'tok', refresh_token: 'rt', token_type: 'bearer' },
    })

    const { verify2FAApi } = await import('../services/authService')
    const result = await verify2FAApi('ct', '123456')

    expect(mockPost).toHaveBeenCalledWith('/api/auth/2fa/verify', {
      challenge_token: 'ct',
      code: '123456',
    })
    expect(result.access_token).toBe('tok')
  })

  it('enroll2FAApi calls the enroll endpoint', async () => {
    mockPost.mockResolvedValueOnce({
      data: { secret: 'SECRET', uri: 'otpauth://...' },
    })

    const { enroll2FAApi } = await import('../services/authService')
    const result = await enroll2FAApi()

    expect(mockPost).toHaveBeenCalledWith('/api/auth/2fa/enroll')
    expect(result.secret).toBe('SECRET')
  })

  it('confirm2FAApi sends TOTP code', async () => {
    mockPost.mockResolvedValueOnce({ data: { activated: true } })

    const { confirm2FAApi } = await import('../services/authService')
    const result = await confirm2FAApi({ code: '654321' })

    expect(mockPost).toHaveBeenCalledWith('/api/auth/2fa/confirm', { code: '654321' })
    expect(result.activated).toBe(true)
  })

  it('forgotPasswordApi sends email', async () => {
    mockPost.mockResolvedValueOnce({
      data: { message: 'If the email exists...', token: null },
    })

    const { forgotPasswordApi } = await import('../services/authService')
    const result = await forgotPasswordApi({ email: 'a@b.com' })

    expect(mockPost).toHaveBeenCalledWith('/api/auth/forgot', { email: 'a@b.com' })
    expect(result.message).toContain('email exists')
  })

  it('resetPasswordApi sends token and new password', async () => {
    mockPost.mockResolvedValueOnce({ data: { message: 'Password updated' } })

    const { resetPasswordApi } = await import('../services/authService')
    const result = await resetPasswordApi({ token: 'tok', new_password: 'newpass' })

    expect(mockPost).toHaveBeenCalledWith('/api/auth/reset', { token: 'tok', new_password: 'newpass' })
    expect(result.message).toBe('Password updated')
  })

  it('impersonateApi sends user_id', async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: 'imp_tok', token_type: 'bearer', impersonating_user_id: 'target-id' },
    })

    const { impersonateApi } = await import('../services/authService')
    const result = await impersonateApi({ user_id: 'target-id' })

    expect(mockPost).toHaveBeenCalledWith('/api/auth/impersonate', { user_id: 'target-id' })
    expect(result.impersonating_user_id).toBe('target-id')
  })

  it('endImpersonationApi calls end endpoint', async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: 'new_tok', refresh_token: '', token_type: 'bearer' },
    })

    const { endImpersonationApi } = await import('../services/authService')
    const result = await endImpersonationApi()

    expect(mockPost).toHaveBeenCalledWith('/api/auth/impersonate/end')
    expect(result.access_token).toBe('new_tok')
  })
})
