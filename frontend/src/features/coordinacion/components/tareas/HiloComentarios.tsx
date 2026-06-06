// features/coordinacion/components/tareas/HiloComentarios.tsx
import { useState } from 'react'
import { useComentarios, useCreateComentario } from '../../hooks/useTareas'

interface Props {
  tareaId: string
}

export function HiloComentarios({ tareaId }: Props) {
  const { data: comentarios = [], isLoading } = useComentarios(tareaId)
  const createComentario = useCreateComentario(tareaId)
  const [contenido, setContenido] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!contenido.trim()) return
    createComentario.mutate(
      { contenido: contenido.trim() },
      { onSuccess: () => setContenido('') },
    )
  }

  if (isLoading) {
    return <p className="text-gray-500 text-sm">Cargando comentarios...</p>
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-gray-700">Comentarios</h4>

      {comentarios.length === 0 ? (
        <p className="text-sm text-gray-400">Sin comentarios todavía.</p>
      ) : (
        <ul className="space-y-2">
          {comentarios.map((c) => (
            <li key={c.id} className="bg-gray-50 rounded p-3 text-sm">
              <span className="font-medium text-gray-800">{c.autor_nombre}</span>
              <span className="text-gray-400 text-xs ml-2">
                {new Date(c.created_at).toLocaleDateString('es-AR')}
              </span>
              <p className="mt-1 text-gray-700">{c.contenido}</p>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <textarea
          value={contenido}
          onChange={(e) => setContenido(e.target.value)}
          rows={2}
          className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
          placeholder="Escribe un comentario..."
        />
        <button
          type="submit"
          disabled={createComentario.isPending || !contenido.trim()}
          className="px-3 py-2 text-xs text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 self-end"
        >
          Enviar
        </button>
      </form>
    </div>
  )
}
