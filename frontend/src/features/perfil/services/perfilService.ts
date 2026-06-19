import { api } from '@/shared/services/api'

export interface PerfilOut {
  id: string
  tenant_id: string
  email: string | null
  nombre: string | null
  apellidos: string | null
  cuil: string | null
  cbu: string | null
  alias_cbu: string | null
  banco: string | null
  regional: string | null
  legajo: string | null
  legajo_profesional: string | null
  facturador: boolean | null
  activo: boolean
  created_at: string
  updated_at: string
}

export interface PerfilUpdate {
  nombre?: string | null
  apellidos?: string | null
  regional?: string | null
  cbu?: string | null
  alias_cbu?: string | null
  banco?: string | null
  facturador?: boolean | null
}

export async function getPerfil(): Promise<PerfilOut> {
  const { data } = await api.get<PerfilOut>('/v1/perfil')
  return data
}

export async function updatePerfil(payload: PerfilUpdate): Promise<PerfilOut> {
  const { data } = await api.patch<PerfilOut>('/v1/perfil', payload)
  return data
}

export interface FacturaMia {
  id: string
  tenant_id: string
  usuario_id: string
  periodo: string
  detalle: string | null
  referencia_archivo: string | null
  tamano_kb: number | null
  estado: string
  cargada_at: string | null
  abonada_at: string | null
}

export interface FacturaMiaCreate {
  periodo: string
  detalle?: string | null
  referencia_archivo?: string | null
  tamano_kb?: number | null
}

export async function getMisFacturas(): Promise<FacturaMia[]> {
  const { data } = await api.get<FacturaMia[]>('/v1/facturas/mias')
  return data
}

export async function crearMiFactura(payload: FacturaMiaCreate): Promise<FacturaMia> {
  const { data } = await api.post<FacturaMia>('/v1/facturas/mias', payload)
  return data
}
