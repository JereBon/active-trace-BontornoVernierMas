// __tests__/exportCsv.test.ts
// TDD tests for exportToCsv utility — RED phase defines expected behavior.

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { exportToCsv } from '@/shared/utils/exportCsv'

// Mock URL.createObjectURL and related DOM APIs
beforeEach(() => {
  // jsdom doesn't implement createObjectURL
  URL.createObjectURL = vi.fn(() => 'blob:mock-url')
  URL.revokeObjectURL = vi.fn()

  const mockAnchor = {
    href: '',
    download: '',
    click: vi.fn(),
  }
  vi.spyOn(document, 'createElement').mockImplementation((tag) => {
    if (tag === 'a') return mockAnchor as unknown as HTMLElement
    return document.createElement(tag)
  })
  vi.spyOn(document.body, 'appendChild').mockImplementation((el) => el)
  vi.spyOn(document.body, 'removeChild').mockImplementation((el) => el)
})

describe('exportToCsv', () => {
  it('generates correct CSV with headers from first row keys', () => {
    const rows = [
      { nombre: 'Juan', email: 'juan@test.com', activo: true },
      { nombre: 'Ana', email: 'ana@test.com', activo: false },
    ]

    let capturedBlob: Blob | null = null
    ;(URL.createObjectURL as ReturnType<typeof vi.fn>).mockImplementation((blob: Blob) => {
      capturedBlob = blob
      return 'blob:mock-url'
    })

    exportToCsv(rows, 'equipos')

    expect(capturedBlob).not.toBeNull()
    return (capturedBlob as unknown as Blob).text().then((text) => {
      const lines = text.split('\n')
      expect(lines[0]).toBe('nombre,email,activo')
      expect(lines[1]).toBe('Juan,juan@test.com,true')
      expect(lines[2]).toBe('Ana,ana@test.com,false')
    })
  })

  it('handles empty array — produces empty file and does not throw', () => {
    let capturedBlob: Blob | null = null
    ;(URL.createObjectURL as ReturnType<typeof vi.fn>).mockImplementation((blob: Blob) => {
      capturedBlob = blob
      return 'blob:mock-url'
    })

    expect(() => exportToCsv([], 'empty')).not.toThrow()

    expect(capturedBlob).not.toBeNull()
    return (capturedBlob as unknown as Blob).text().then((text) => {
      expect(text).toBe('')
    })
  })

  it('appends .csv extension if not already present', () => {
    const mockAnchor = { href: '', download: '', click: vi.fn() }
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as unknown as HTMLElement)

    exportToCsv([{ a: 1 }], 'reporte')
    expect(mockAnchor.download).toBe('reporte.csv')
  })

  it('does not double-append .csv if already present', () => {
    const mockAnchor = { href: '', download: '', click: vi.fn() }
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as unknown as HTMLElement)

    exportToCsv([{ a: 1 }], 'equipos.csv')
    expect(mockAnchor.download).toBe('equipos.csv')
  })

  it('escapes values containing commas with double quotes', () => {
    const rows = [{ nombre: 'López, Juan' }]

    let capturedBlob: Blob | null = null
    ;(URL.createObjectURL as ReturnType<typeof vi.fn>).mockImplementation((blob: Blob) => {
      capturedBlob = blob
      return 'blob:mock-url'
    })

    exportToCsv(rows, 'test')

    return (capturedBlob as unknown as Blob).text().then((text) => {
      const dataLine = text.split('\n')[1]
      expect(dataLine).toBe('"López, Juan"')
    })
  })
})
