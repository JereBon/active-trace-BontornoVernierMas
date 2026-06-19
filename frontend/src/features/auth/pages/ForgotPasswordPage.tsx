import { useState } from 'react'
import { Link } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { Spinner } from '@/shared/components/Spinner'

export function ForgotPasswordPage() {
  const { forgotPassword } = useAuth()
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [resetToken, setResetToken] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return

    setIsSubmitting(true)
    setError('')

    try {
      const result = await forgotPassword(email)
      setSent(true)
      if (result.token) {
        setResetToken(result.token)
      }
    } catch (err: unknown) {
      let message = 'Error al solicitar recuperación'
      if (isAxiosError(err) && err.response?.data && typeof err.response.data === 'object') {
        const detail = (err.response.data as Record<string, unknown>).detail
        message = typeof detail === 'string' ? detail : message
      } else if (err instanceof Error) {
        message = err.message
      }
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (sent) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-8 shadow-sm text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900">Correo enviado</h2>
          <p className="mt-2 text-sm text-gray-500">
            Si existe una cuenta con ese email, vas a recibir un enlace para restablecer tu contraseña.
          </p>
          {resetToken && (
            <div className="mt-4 rounded-lg bg-gray-50 p-3 text-left">
              <p className="mb-1 text-xs font-medium text-gray-500">MODO DEV — Token generado:</p>
              <p className="break-all font-mono text-xs text-gray-700">{resetToken}</p>
              <Link
                to={`/reset-password?token=${encodeURIComponent(resetToken)}`}
                className="mt-2 inline-block text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                Ir a restablecer contraseña →
              </Link>
            </div>
          )}
          <Link
            to="/login"
            className="mt-6 inline-block text-sm font-medium text-brand-600 hover:text-brand-700"
          >
            Volver al inicio de sesión
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-brand-700">activia-trace</h1>
          <p className="mt-1 text-sm text-gray-500">Recuperar contraseña</p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
          <h2 className="mb-2 text-lg font-semibold text-gray-900">
            Olvidaste tu contraseña
          </h2>
          <p className="mb-6 text-sm text-gray-500">
            Ingresá tu email y te enviaremos un enlace para restablecerla.
          </p>

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
              />
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 px-3 py-2">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={!email || isSubmitting}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {isSubmitting ? <Spinner size="sm" /> : null}
              {isSubmitting ? 'Enviando…' : 'Enviar enlace'}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-500">
            <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
              Volver al inicio de sesión
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
