import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { TwoFaChallengePlaceholder } from '@/features/auth/components/TwoFaChallengePlaceholder'
import { Spinner } from '@/shared/components/Spinner'

// ---------------------------------------------------------------------------
// Zod schema — strict, no extra fields
// ---------------------------------------------------------------------------
const loginSchema = z
  .object({
    email: z.string().email('Ingresá un email válido'),
    password: z.string().min(1, 'La contraseña es requerida'),
  })
  .strict()

type LoginFormValues = z.infer<typeof loginSchema>

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function LoginPage() {
  const { isAuthenticated, isLoading, challenge, login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  })

  // If already authenticated, redirect away from login
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      const next = searchParams.get('next') ?? '/dashboard'
      navigate(next, { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate, searchParams])

  // While checking stored session
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Spinner />
      </div>
    )
  }

  // 2FA challenge screen
  if (challenge) {
    return <TwoFaChallengePlaceholder challengeToken={challenge.challenge_token} />
  }

  const onSubmit = async (values: LoginFormValues) => {
    try {
      await login(values)
      // navigation happens via the useEffect above once isAuthenticated becomes true
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Error al iniciar sesión'
      setError('root', { message })
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo / brand */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-brand-700">activia-trace</h1>
          <p className="mt-1 text-sm text-gray-500">Gestión académica y trazabilidad</p>
        </div>

        {/* Card */}
        <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
          <h2 className="mb-6 text-lg font-semibold text-gray-900">Iniciar sesión</h2>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                {...register('email')}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Contraseña
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                {...register('password')}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
              />
              {errors.password && (
                <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
              )}
            </div>

            {/* Server error */}
            {errors.root && (
              <div className="rounded-lg bg-red-50 px-3 py-2">
                <p className="text-sm text-red-700">{errors.root.message}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {isSubmitting ? <Spinner size="sm" /> : null}
              {isSubmitting ? 'Ingresando…' : 'Ingresar'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
