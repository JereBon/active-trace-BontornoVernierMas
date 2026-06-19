import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { api } from '@/shared/services/api'
import { Spinner } from '@/shared/components/Spinner'

interface UserOption {
  id: string
  nombre: string
  apellidos: string
  email: string
}

const composeSchema = z
  .object({
    destinatario_id: z.string().uuid('Seleccioná un destinatario'),
    asunto: z.string().min(1, 'El asunto es requerido').max(255),
    cuerpo: z.string().min(1, 'El mensaje no puede estar vacío'),
  })
  .strict()

type ComposeFormValues = z.infer<typeof composeSchema>

interface ComposeMessageModalProps {
  onSend: (data: ComposeFormValues) => Promise<void>
  onClose: () => void
}

export function ComposeMessageModal({
  onSend,
  onClose,
}: ComposeMessageModalProps) {
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserOption | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const { data: users = [] } = useQuery<UserOption[]>({
    queryKey: ['usuarios-search'],
    queryFn: async () => {
      const { data } = await api.get<UserOption[]>('/v1/usuarios/search')
      return data
    },
  })

  const filtered = search
    ? users.filter(
        (u) =>
          u.nombre.toLowerCase().includes(search.toLowerCase()) ||
          u.apellidos.toLowerCase().includes(search.toLowerCase()) ||
          u.email.toLowerCase().includes(search.toLowerCase()),
      )
    : users

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ComposeFormValues>({
    resolver: zodResolver(composeSchema),
  })

  const onSubmit = async (values: ComposeFormValues) => {
    setSending(true)
    setError('')
    try {
      await onSend(values)
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'Error al enviar el mensaje',
      )
    } finally {
      setSending(false)
    }
  }

  const handleSelectUser = (u: UserOption) => {
    setSelectedUser(u)
    setValue('destinatario_id', u.id)
    setSearch(`${u.nombre} ${u.apellidos}`)
    setShowDropdown(false)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Nuevo mensaje
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4 p-6">
          <div className="relative" ref={dropdownRef}>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Destinatario
            </label>
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setSelectedUser(null)
                setValue('destinatario_id', '')
                setShowDropdown(true)
              }}
              onFocus={() => setShowDropdown(true)}
              placeholder="Buscá por nombre, apellido o email…"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
            />
            {selectedUser && (
              <p className="mt-1 text-xs text-green-600">
                ✓ {selectedUser.nombre} {selectedUser.apellidos} ({selectedUser.email})
              </p>
            )}
            {showDropdown && (
              <div className="absolute z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
                {filtered.length === 0 ? (
                  <p className="px-3 py-2 text-sm text-gray-400">Sin resultados</p>
                ) : (
                  filtered.map((u) => (
                    <button
                      key={u.id}
                      type="button"
                      onClick={() => handleSelectUser(u)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 transition"
                    >
                      <span className="font-medium text-gray-900">
                        {u.nombre} {u.apellidos}
                      </span>
                      <span className="ml-2 text-xs text-gray-400">{u.email}</span>
                    </button>
                  ))
                )}
              </div>
            )}
            <input type="hidden" {...register('destinatario_id')} />
            {errors.destinatario_id && (
              <p className="mt-1 text-xs text-red-600">
                {errors.destinatario_id.message}
              </p>
            )}
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Asunto
            </label>
            <input
              type="text"
              {...register('asunto')}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
            />
            {errors.asunto && (
              <p className="mt-1 text-xs text-red-600">
                {errors.asunto.message}
              </p>
            )}
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Mensaje
            </label>
            <textarea
              rows={5}
              {...register('cuerpo')}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
            />
            {errors.cuerpo && (
              <p className="mt-1 text-xs text-red-600">
                {errors.cuerpo.message}
              </p>
            )}
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 px-3 py-2">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={sending}
              className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {sending ? <Spinner size="sm" /> : null}
              {sending ? 'Enviando…' : 'Enviar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
