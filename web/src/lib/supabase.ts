import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.PUBLIC_SUPABASE_URL ?? "";
const supabaseKey = import.meta.env.PUBLIC_SUPABASE_ANON_KEY ?? "";

export const supabase = createClient(supabaseUrl, supabaseKey);

// ── Tipos ──────────────────────────────────────────────────────────────────

export interface Municipio {
  id: string;
  nombre: string;
  nombre_alt: string | null;
  slug: string;
  provincia: string;
  comunidad: string;
  poblacion: number | null;
  n_concejales: number | null;
  alcalde: string | null;
  partido_gobierno: string | null;
  color_gobierno: string | null;
  web_oficial: string | null;
  url_actas: string | null;
}

export interface Pleno {
  id: string;
  municipio_id: string;
  numero_acta: number;
  fecha: string;
  tipo_sesion: "ordinaria" | "extraordinaria" | "urgente";
  resumen_ia: string | null;
  n_puntos: number | null;
  n_asistentes: number | null;
  municipio: string;
  estado: string;
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

// ── Municipios ─────────────────────────────────────────────────────────────

export async function getMunicipios(): Promise<Municipio[]> {
  try {
    const { data } = await supabase
      .from("municipios")
      .select("*")
      .eq("activo", true)
      .order("nombre");
    return data ?? [];
  } catch {
    return [];
  }
}

export async function getMunicipio(slug: string): Promise<Municipio | null> {
  try {
    const { data } = await supabase
      .from("municipios")
      .select("*")
      .eq("slug", slug)
      .single();
    return data;
  } catch {
    return null;
  }
}

export async function getStatsMunicipio(municipioId: string) {
  try {
    const [plenosRes, puntosRes] = await Promise.all([
      supabase
        .from("plenos")
        .select("id, fecha", { count: "exact" })
        .eq("municipio_id", municipioId)
        .eq("estado", "procesado")
        .order("fecha", { ascending: false })
        .limit(1),
      supabase
        .from("puntos")
        .select("id", { count: "exact", head: true })
        .in(
          "pleno_id",
          (
            await supabase
              .from("plenos")
              .select("id")
              .eq("municipio_id", municipioId)
              .eq("estado", "procesado")
          ).data?.map((p) => p.id) ?? []
        ),
    ]);
    return {
      totalPlenos: plenosRes.count ?? 0,
      ultimaFecha: plenosRes.data?.[0]?.fecha ?? null,
      totalPuntos: puntosRes.count ?? 0,
    };
  } catch {
    return { totalPlenos: 0, ultimaFecha: null, totalPuntos: 0 };
  }
}

// ── Plenos ─────────────────────────────────────────────────────────────────

export async function getPlenos(limit = 20): Promise<Pleno[]> {
  try {
    const { data } = await supabase
      .from("v_plenos")
      .select("*")
      .eq("estado", "procesado")
      .order("fecha", { ascending: false })
      .limit(limit);
    return data ?? [];
  } catch {
    return [];
  }
}

export async function getPleno(id: string): Promise<Pleno | null> {
  try {
    const { data } = await supabase
      .from("v_plenos")
      .select("*")
      .eq("id", id)
      .single();
    return data;
  } catch {
    return null;
  }
}

export async function getPlenosByMunicipio(
  municipioId: string,
  page = 1,
  pageSize = 20
): Promise<{ data: Pleno[]; count: number }> {
  try {
    const offset = (page - 1) * pageSize;
    const { data, count } = await supabase
      .from("v_plenos")
      .select("*", { count: "exact" })
      .eq("municipio_id", municipioId)
      .eq("estado", "procesado")
      .order("fecha", { ascending: false })
      .range(offset, offset + pageSize - 1);
    return { data: data ?? [], count: count ?? 0 };
  } catch {
    return { data: [], count: 0 };
  }
}

export async function getPlenosFiltrados(params: {
  categoria?: string;
  municipio?: string;
  page?: number;
}): Promise<{ data: Pleno[]; count: number }> {
  try {
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
  } catch {
    return { data: [], count: 0 };
  }
}

// ── Puntos ─────────────────────────────────────────────────────────────────

export async function getPuntosPleno(plenoId: string): Promise<Punto[]> {
  try {
    const { data } = await supabase
      .from("puntos")
      .select("*")
      .eq("pleno_id", plenoId)
      .order("numero");
    return data ?? [];
  } catch {
    return [];
  }
}

export async function getPuntosRelevantes(limit = 12): Promise<any[]> {
  try {
    const { data } = await supabase
      .from("v_puntos_relevantes")
      .select("*")
      .limit(limit);
    return data ?? [];
  } catch {
    return [];
  }
}

export async function getVotacionesPunto(puntoId: string): Promise<Votacion[]> {
  try {
    const { data } = await supabase
      .from("votaciones")
      .select(`votos_favor, votos_contra, abstenciones, partidos ( nombre, siglas, color_hex )`)
      .eq("punto_id", puntoId);
    return (data ?? []).map((v: any) => ({
      partido: v.partidos.nombre,
      siglas: v.partidos.siglas,
      color_hex: v.partidos.color_hex,
      votos_favor: v.votos_favor,
      votos_contra: v.votos_contra,
      abstenciones: v.abstenciones,
    }));
  } catch {
    return [];
  }
}

// ── Constantes UI ──────────────────────────────────────────────────────────

export const CATEGORIAS: Record<string, string> = {
  urbanismo:         "Urbanismo",
  vivienda:          "Vivienda",
  hacienda:          "Hacienda",
  medio_ambiente:    "Medio Ambiente",
  servicios_sociales:"Servicios Sociales",
  movilidad:         "Movilidad",
  cultura:           "Cultura",
  derechos:          "Derechos",
  gobernanza:        "Gobernanza",
  seguridad:         "Seguridad",
  educacion:         "Educación",
  otro:              "Otro",
};

export const TIPO_LABEL: Record<string, string> = {
  dar_cuenta:                "Dar cuenta",
  aprobacion_definitiva:     "Aprobación definitiva",
  aprobacion_inicial:        "Aprobación inicial",
  proposicion_normativa:     "Proposición normativa",
  declaracion_institucional: "Declaración institucional",
  mocion:                    "Moción",
  interpelacion:             "Interpelación",
  pregunta_oral:             "Pregunta oral",
  otro:                      "Trámite",
};

export const RESULTADO_LABEL: Record<string, string> = {
  aprobado:     "Aprobado",
  rechazado:    "Rechazado",
  enterado:     "Enterado",
  retirado:     "Retirado",
  aplazado:     "Aplazado",
  sin_votacion: "Sin votación",
};
