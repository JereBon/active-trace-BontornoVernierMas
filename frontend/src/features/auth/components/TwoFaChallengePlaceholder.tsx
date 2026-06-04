interface TwoFaChallengePlaceholderProps {
  challengeToken: string
}

export function TwoFaChallengePlaceholder({
  challengeToken: _challengeToken,
}: TwoFaChallengePlaceholderProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
        <h2 className="mb-2 text-xl font-semibold text-gray-900">
          Verificación en dos pasos
        </h2>
        <p className="mb-6 text-sm text-gray-500">
          2FA — próximamente. Esta funcionalidad estará disponible en la
          próxima versión.
        </p>
        <input
          type="text"
          inputMode="numeric"
          maxLength={6}
          placeholder="Código TOTP"
          disabled
          className="w-full rounded-lg border border-gray-300 bg-gray-100 px-3 py-2 text-center text-lg tracking-widest text-gray-400 outline-none"
        />
        <p className="mt-4 text-center text-xs text-gray-400">
          Ingresá el código de 6 dígitos de tu app de autenticación
        </p>
      </div>
    </div>
  )
}
