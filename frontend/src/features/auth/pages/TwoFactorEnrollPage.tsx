import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { Spinner } from '@/shared/components/Spinner'

type Step = 'idle' | 'loading' | 'show_secret' | 'confirming' | 'done' | 'error'

export function TwoFactorEnrollPage() {
  const { user, enrollTOTP, confirmTOTP } = useAuth()
  const [step, setStep] = useState<Step>('idle')
  const [secret, setSecret] = useState('')
  const [uri, setUri] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState('')

  const handleEnroll = async () => {
    setStep('loading')
    setError('')
    try {
      const result = await enrollTOTP()
      setSecret(result.secret)
      setUri(result.uri)
      setStep('show_secret')
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'Error al generar el código 2FA',
      )
      setStep('error')
    }
  }

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault()
    if (code.length !== 6) return

    setStep('confirming')
    setError('')
    try {
      await confirmTOTP(code)
      setStep('done')
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Código inválido'
      setError(message)
      setStep('show_secret')
    }
  }

  const qrCodeUrl =
    uri
      ? `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(uri)}`
      : null

  if (user?.totp_activo && step === 'idle') {
    return (
      <div className="mx-auto max-w-lg space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Autenticación en dos pasos (2FA)
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Vinculá tu cuenta con una app de autenticación como Google
            Authenticator o Authy.
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">
            2FA ya está activado
          </h3>
          <p className="mt-2 text-sm text-gray-500">
            La autenticación en dos pasos ya está configurada en tu cuenta.
          </p>
          <Link
            to="/perfil"
            className="mt-6 inline-block rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Volver a mi perfil
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Autenticación en dos pasos (2FA)
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Vinculá tu cuenta con una app de autenticación como Google
          Authenticator o Authy.
        </p>
      </div>

      {step === 'idle' && (
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <p className="mb-4 text-sm text-gray-600">
            La autenticación en dos pasos agrega una capa extra de seguridad a
            tu cuenta. Cada vez que inicies sesión, vas a necesitar un código
            de 6 dígitos generado por tu app de autenticación.
          </p>
          <button
            onClick={handleEnroll}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Activar 2FA
          </button>
        </div>
      )}

      {step === 'loading' && (
        <div className="flex items-center justify-center rounded-xl border border-gray-200 bg-white p-12">
          <Spinner size="lg" />
        </div>
      )}

      {step === 'show_secret' && (
        <div className="space-y-6 rounded-xl border border-gray-200 bg-white p-6">
          <div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              1. Escaneá el código QR
            </h3>
            <p className="mb-4 text-sm text-gray-500">
              Usá tu app de autenticación para escanear este código QR. Si no
              podés escanearlo, ingresá la clave manualmente.
            </p>

            {qrCodeUrl && (
              <div className="flex justify-center">
                <img
                  src={qrCodeUrl}
                  alt="Código QR para 2FA"
                  className="h-48 w-48 rounded-lg border border-gray-200"
                />
              </div>
            )}

            <div className="mt-4 rounded-lg bg-gray-50 p-3">
              <p className="mb-1 text-xs font-medium text-gray-500">
                Clave secreta (ingresá manualmente si no podés escanear):
              </p>
              <p className="select-all font-mono text-sm text-gray-900">
                {secret}
              </p>
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              2. Verificá el código
            </h3>
            <p className="mb-4 text-sm text-gray-500">
              Ingresá el código de 6 dígitos que aparece en tu app para
              confirmar que está configurado correctamente.
            </p>

            <form onSubmit={handleConfirm} noValidate className="space-y-4">
              <div>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={code}
                  onChange={(e) =>
                    setCode(e.target.value.replace(/\D/g, ''))
                  }
                  placeholder="000000"
                  autoFocus
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-center text-lg tracking-widest outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                />
              </div>

              {error && (
                <div className="rounded-lg bg-red-50 px-3 py-2">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={code.length !== 6 || step === 'confirming'}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700 disabled:opacity-60"
              >
                {step === 'confirming' ? <Spinner size="sm" /> : null}
                {step === 'confirming'
                  ? 'Verificando…'
                  : 'Verificar y activar'}
              </button>
            </form>
          </div>
        </div>
      )}

      {step === 'done' && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">
            2FA activado correctamente
          </h3>
          <p className="mt-2 text-sm text-gray-500">
            A partir del próximo inicio de sesión, vas a necesitar tu código
            de autenticación.
          </p>
          <Link
            to="/perfil"
            className="mt-6 inline-block rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Volver a mi perfil
          </Link>
        </div>
      )}

      {step === 'error' && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-sm text-red-700">{error}</p>
          <button
            onClick={handleEnroll}
            className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Intentar de nuevo
          </button>
        </div>
      )}
    </div>
  )
}
