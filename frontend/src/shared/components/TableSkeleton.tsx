interface TableSkeletonProps {
  rows?: number
  cols?: number
}

export function TableSkeleton({ rows = 5, cols = 4 }: TableSkeletonProps) {
  return (
    <div className="animate-pulse" aria-busy="true" aria-label="Cargando datos...">
      {/* Header */}
      <div className="flex gap-3 mb-3 px-2">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-4 bg-gray-200 rounded flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, r) => (
        <div
          key={r}
          className="flex gap-3 px-2 py-3 border-t border-gray-100"
        >
          {Array.from({ length: cols }).map((_, c) => (
            <div
              key={c}
              className="h-4 bg-gray-100 rounded flex-1"
              style={{ opacity: 1 - r * 0.12 }}
            />
          ))}
        </div>
      ))}
    </div>
  )
}
