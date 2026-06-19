import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getColoquiosDisponibles, getMisReservas, crearReserva, cancelarReserva } from '../services/coloquiosAlumnoService'
import { useAuth } from '@/features/auth/hooks/useAuth'

export function ColoquiosAlumnoPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data: disponibles = [], isLoading: loadingDisponibles } = useQuery({
    queryKey: ['coloquios-disponibles'],
    queryFn: getColoquiosDisponibles,
  })

  const { data: misReservas = [], isLoading: loadingReservas } = useQuery({
    queryKey: ['mis-reservas'],
    queryFn: getMisReservas,
  })

  const reservarMut = useMutation({
    mutationFn: ({ evaluacionId, fecha_hora }: { evaluacionId: string; fecha_hora: string }) =>
      crearReserva(evaluacionId, fecha_hora),
    onSuccess: () => {
      setSelectedId(null)
      queryClient.invalidateQueries({ queryKey: ['coloquios-disponibles'] })
      queryClient.invalidateQueries({ queryKey: ['mis-reservas'] })
    },
  })

  const cancelarMut = useMutation({
    mutationFn: ({ evaluacionId, reservaId }: { evaluacionId: string; reservaId: string }) =>
      cancelarReserva(evaluacionId, reservaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios-disponibles'] })
      queryClient.invalidateQueries({ queryKey: ['mis-reservas'] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Coloquios</h1>
        <p className="mt-1 text-sm text-gray-500">
          Reservá tu turno para los coloquios disponibles.
        </p>
      </div>

      {/* Available coloquios */}
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Convocatorias abiertas</h2>
        {loadingDisponibles ? (
          <p className="text-sm text-gray-400">Cargando…</p>
        ) : disponibles.length === 0 ? (
          <p className="text-sm text-gray-400">No hay coloquios disponibles en este momento.</p>
        ) : (
          <div className="space-y-3">
            {disponibles.map((c) => (
              <div key={c.id} className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
                <div>
                  <p className="text-sm font-medium text-gray-900">{c.instancia}</p>
                  <p className="text-xs text-gray-500">
                    Cupos disponibles: <strong>{c.cupos_disponibles}</strong> | Tipo: {c.tipo}
                  </p>
                </div>
                {selectedId === c.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="datetime-local"
                      onChange={(e) => {
                        if (e.target.value) {
                          reservarMut.mutate({ evaluacionId: c.id, fecha_hora: new Date(e.target.value).toISOString() })
                        }
                      }}
                      className="rounded border border-gray-300 px-2 py-1 text-sm"
                    />
                    <button
                      onClick={() => setSelectedId(null)}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      Cancelar
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setSelectedId(c.id)}
                    disabled={c.cupos_disponibles <= 0 || reservarMut.isPending}
                    className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-40"
                  >
                    Reservar
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* My reservations */}
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Mis reservas</h2>
        {loadingReservas ? (
          <p className="text-sm text-gray-400">Cargando…</p>
        ) : misReservas.length === 0 ? (
          <p className="text-sm text-gray-400">No tenés reservas activas.</p>
        ) : (
          <div className="space-y-2">
            {misReservas.map((r) => (
              <div key={r.id} className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 p-3">
                <div>
                  <p className="text-sm text-gray-700">
                    {new Date(r.fecha_hora).toLocaleString('es-AR', {
                      day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
                    })}
                  </p>
                  <span className={`inline-block mt-1 rounded px-2 py-0.5 text-xs font-medium ${
                    r.estado === 'Activa' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-500'
                  }`}>{r.estado}</span>
                </div>
                {r.estado === 'Activa' && (
                  <button
                    onClick={() => cancelarMut.mutate({ evaluacionId: r.evaluacion_id, reservaId: r.id })}
                    disabled={cancelarMut.isPending}
                    className="rounded border border-red-300 px-2 py-1 text-xs text-red-600 hover:bg-red-50 disabled:opacity-40"
                  >
                    Cancelar
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
