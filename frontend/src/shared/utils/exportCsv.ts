// shared/utils/exportCsv.ts
// Client-side CSV export — no backend endpoint needed.

/**
 * Converts an array of records to CSV and triggers a browser download.
 * Headers are derived from the keys of the first row.
 * Empty arrays produce a file with only the header row (empty string if no rows at all).
 */
export function exportToCsv(rows: Record<string, unknown>[], filename: string): void {
  if (rows.length === 0) {
    const blob = new Blob([''], { type: 'text/csv;charset=utf-8;' })
    triggerDownload(blob, filename)
    return
  }

  const headers = Object.keys(rows[0])
  const escape = (value: unknown): string => {
    const str = value === null || value === undefined ? '' : String(value)
    // Wrap in quotes if the value contains commas, quotes, or newlines
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`
    }
    return str
  }

  const csvLines = [
    headers.join(','),
    ...rows.map((row) => headers.map((h) => escape(row[h])).join(',')),
  ]

  const blob = new Blob([csvLines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  triggerDownload(blob, filename)
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename.endsWith('.csv') ? filename : `${filename}.csv`
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}
