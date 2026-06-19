import { useState } from 'react'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { Spinner } from '@/shared/components/Spinner'

interface TwoFaChallengePlaceholderProps {
  challengeToken: string
}

export function TwoFaChallengePlaceholder({
  challengeToken: _challengeToken,
}: TwoFaChallengePlaceholderProps) {
  const { verify2FA } = useAuth()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (code.length !== 6) return

    setIsSubmitting(true)
    setError('')

    try {
      await verify2FA(code)
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Código inválido. Intentá de nuevo.'
      setError(message)
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
        <h2 className="mb-2 text-xl font-semibold text-gray-900">
          Verificación en dos pasos
        </h2>
        <p className="mb-6 text-sm text-gray-500">
          Ingresá el código de 6 dígitos de tu app de autenticación.
        </p>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <div>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
              placeholder="000000"
              disabled={isSubmitting}
              autoFocus
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-center text-lg tracking-widest outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 disabled:bg-gray-100 disabled:text-gray-400"
            />
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 px-3 py-2">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={code.length !== 6 || isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700 disabled:opacity-60"
          >
            {isSubmitting ? <Spinner size="sm" /> : null}
            {isSubmitting ? 'Verificando…' : 'Verificar'}
          </button>
        </form>
      </div>
    </div>
  )
}
