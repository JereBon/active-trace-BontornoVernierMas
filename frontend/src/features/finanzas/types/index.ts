// features/finanzas/types/index.ts
// TypeScript types for C-24 frontend-finanzas-y-admin — mirrors backend schemas (C-18)

// ─── Liquidaciones ────────────────────────────────────────────────────────────

export type LiquidacionEstado = 'abierta' | 'cerrada'

export interface LiquidacionRow {
  id: string
  usuario_id: string
  nombre_docente: string
  rol: string
  es_nexo: boolean
  es_facturante: boolean
  periodo: string
  cohorte_id: string
  monto_base: number
  monto_plus: number
  monto_total: number
  estado: LiquidacionEstado
  created_at: string
}

export interface VistaPeriodoKPIs {
  total_sin_factura: number
  total_con_factura: number
  cantidad_docentes: number
  cantidad_nexos: number
}

export interface VistaPeriodoOut {
  general: LiquidacionRow[]
  nexo: LiquidacionRow[]
  facturantes: LiquidacionRow[]
  kpis: VistaPeriodoKPIs
}

export interface CalcularRequest {
  cohorte_id: string
  periodo: string
}

export interface CalcularResponse {
  registros_creados: number
  periodo: string
  cohorte_id: string
}

export interface CerrarRequest {
  cohorte_id: string
  periodo: string
}

export interface CerrarResponse {
  registros_cerrados: number
  periodo: string
  cohorte_id: string
}

// ─── Grilla Salarial ──────────────────────────────────────────────────────────

export interface SalarioBase {
  id: string
  rol: string
  monto: number
  vigencia_desde: string
  vigencia_hasta: string | null
  tenant_id: string
  created_at: string
}

export interface SalarioBaseCreate {
  rol: string
  monto: number
  vigencia_desde: string
  vigencia_hasta?: string | null
}

export interface SalarioBaseUpdate {
  rol?: string
  monto?: number
  vigencia_desde?: string
  vigencia_hasta?: string | null
}

export interface SalarioPlus {
  id: string
  grupo: string
  rol: string
  monto: number
  vigencia_desde: string
  vigencia_hasta: string | null
  tenant_id: string
  created_at: string
}

export interface SalarioPlusCreate {
  grupo: string
  rol: string
  monto: number
  vigencia_desde: string
  vigencia_hasta?: string | null
}

export interface SalarioPlusUpdate {
  grupo?: string
  rol?: string
  monto?: number
  vigencia_desde?: string
  vigencia_hasta?: string | null
}

// ─── Facturas ─────────────────────────────────────────────────────────────────

export type FacturaEstado = 'pendiente' | 'abonada'

export interface Factura {
  id: string
  usuario_id: string
  nombre_docente: string
  periodo: string
  monto: number
  estado: FacturaEstado
  numero: string | null
  fecha_emision: string | null
  fecha_abono: string | null
  tenant_id: string
  created_at: string
}

export interface FacturaCreate {
  usuario_id: string
  periodo: string
  monto: number
  numero?: string | null
  fecha_emision?: string | null
}

export interface FacturaEstadoUpdate {
  estado: FacturaEstado
}

export interface FacturaFiltros {
  usuario_id?: string
  periodo?: string
  estado?: FacturaEstado
}
