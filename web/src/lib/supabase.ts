import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.PUBLIC_SUPABASE_URL;
const supabaseKey = import.meta.env.PUBLIC_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseKey);

// ── Tipos ──────────────────────────────────────────────────────────────────

export interface Pleno {
  id: string;
  numero_acta: number;
  fecha: string;
  tipo_sesion: "ordinaria" | "extraordinaria" | "urgente";
  resumen_ia: string | null;
  n_puntos: number | null;
  n_asistentes: number | null;
  municipio: string;
  total_puntos: number;
  aprobados: number;
  rechazados: number;
  unanimes: number;
}

export interface Punto {
  id: string;
  pleno_id: string;
  numero: number;
  titulo: string;
  comision: string;
  tipo: string;
  categoria: string;
  resultado: string;
  unanimidad: boolean | null;
  resumen_ia: string | null;
  relevancia_social: number | null;
  es_urgencia: boolean;
}

export interface Votacion {
  partido: string;
  siglas: string;
  color_hex: string;
  votos_favor: number;
  votos_contra: number;
  abstenciones: number;
}

// ── Queries ────────────────────────────────────────────────────────────────

export async function getPlenos(limit = 20): Promise<Pleno[]> {
  const { data } = await supabase
    .from("v_plenos")
    .select("*")
    .eq("estado", "procesado")
    .order("fecha", { ascending: false })
    .limit(limit);
  return data ?? [];
}

export async function getPleno(id: string): Promise<Pleno | null> {
  const { data } = await supabase
    .from("v_plenos")
    .select("*")
    .eq("id", id)
    .single();
  return data;
}

export async function getPuntosPleno(plenoId: string): Promise<Punto[]> {
  const { data } = await supabase
    .from("puntos")
    .select("*")
    .eq("pleno_id", plenoId)
    .order("numero");
  return data ?? [];
}

export async function getPuntosRelevantes(limit = 12): Promise<any[]> {
  const { data } = await supabase
    .from("v_puntos_relevantes")
    .select("*")
    .limit(limit);
  return data ?? [];
}

export async function getVotacionesPunto(puntoId: string): Promise<Votacion[]> {
  const { data } = await supabase
    .from("votaciones")
    .select(`
      votos_favor, votos_contra, abstenciones,
      partidos ( nombre, siglas, color_hex )
    `)
    .eq("punto_id", puntoId);
  return (data ?? []).map((v: any) => ({
    partido: v.partidos.nombre,
    siglas: v.partidos.siglas,
    color_hex: v.partidos.color_hex,
    votos_favor: v.votos_favor,
    votos_contra: v.votos_contra,
    abstenciones: v.abstenciones,
  }));
}

export async function getPlenosFiltrados(params: {
  categoria?: string;
  municipio?: string;
  desde?: string;
  hasta?: string;
  q?: string;
  page?: number;
}): Promise<{ data: Pleno[]; count: number }> {
  const PAGE_SIZE = 20;
  const offset = ((params.page ?? 1) - 1) * PAGE_SIZE;

  let query = supabase
    .from("v_plenos")
    .select("*", { count: "exact" })
    .eq("estado", "procesado");

  if (params.municipio) query = query.eq("municipio", params.municipio);

  const { data, count } = await query
    .order("fecha", { ascending: false })
    .range(offset, offset + PAGE_SIZE - 1);

  return { data: data ?? [], count: count ?? 0 };
}

export const CATEGORIAS: Record<string, string> = {
  urbanismo: "Urbanismo",
  vivienda: "Vivienda",
  hacienda: "Hacienda",
  medio_ambiente: "Medio Ambiente",
  servicios_sociales: "Servicios Sociales",
  movilidad: "Movilidad",
  cultura: "Cultura",
  derechos: "Derechos",
  gobernanza: "Gobernanza",
  seguridad: "Seguridad",
  educacion: "Educación",
  otro: "Otro",
};
