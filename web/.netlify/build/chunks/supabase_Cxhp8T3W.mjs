import { createClient } from '@supabase/supabase-js';

const supabaseUrl = "";
const supabaseKey = "";
const supabase = createClient(supabaseUrl, supabaseKey);
async function getMunicipios() {
  try {
    const { data } = await supabase.from("municipios").select("*").eq("activo", true).order("nombre");
    return data ?? [];
  } catch {
    return [];
  }
}
async function getMunicipio(slug) {
  try {
    const { data } = await supabase.from("municipios").select("*").eq("slug", slug).single();
    return data;
  } catch {
    return null;
  }
}
async function getPleno(id) {
  try {
    const { data } = await supabase.from("v_plenos").select("*").eq("id", id).single();
    return data;
  } catch {
    return null;
  }
}
async function getPlenosByMunicipio(municipioId, page = 1, pageSize = 20) {
  try {
    const offset = (page - 1) * pageSize;
    const { data, count } = await supabase.from("v_plenos").select("*", { count: "exact" }).eq("municipio_id", municipioId).eq("estado", "procesado").order("fecha", { ascending: false }).range(offset, offset + pageSize - 1);
    return { data: data ?? [], count: count ?? 0 };
  } catch {
    return { data: [], count: 0 };
  }
}
async function getPlenosFiltrados(params) {
  try {
    const PAGE_SIZE = 20;
    const offset = ((params.page ?? 1) - 1) * PAGE_SIZE;
    let query = supabase.from("v_plenos").select("*", { count: "exact" }).eq("estado", "procesado");
    if (params.municipio) query = query.eq("municipio", params.municipio);
    const { data, count } = await query.order("fecha", { ascending: false }).range(offset, offset + PAGE_SIZE - 1);
    return { data: data ?? [], count: count ?? 0 };
  } catch {
    return { data: [], count: 0 };
  }
}
async function getPuntosPleno(plenoId) {
  try {
    const { data } = await supabase.from("puntos").select("*").eq("pleno_id", plenoId).order("numero");
    return data ?? [];
  } catch {
    return [];
  }
}
async function getVotacionesPunto(puntoId) {
  try {
    const { data } = await supabase.from("votaciones").select(`votos_favor, votos_contra, abstenciones, partidos ( nombre, siglas, color_hex )`).eq("punto_id", puntoId);
    return (data ?? []).map((v) => ({
      partido: v.partidos.nombre,
      siglas: v.partidos.siglas,
      color_hex: v.partidos.color_hex,
      votos_favor: v.votos_favor,
      votos_contra: v.votos_contra,
      abstenciones: v.abstenciones
    }));
  } catch {
    return [];
  }
}
const CATEGORIAS = {
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
  otro: "Otro"
};
const TIPO_LABEL = {
  dar_cuenta: "Dar cuenta",
  aprobacion_definitiva: "Aprobación definitiva",
  aprobacion_inicial: "Aprobación inicial",
  proposicion_normativa: "Proposición normativa",
  declaracion_institucional: "Declaración institucional",
  mocion: "Moción",
  interpelacion: "Interpelación",
  pregunta_oral: "Pregunta oral",
  otro: "Trámite"
};
const RESULTADO_LABEL = {
  aprobado: "Aprobado",
  rechazado: "Rechazado",
  enterado: "Enterado",
  retirado: "Retirado",
  aplazado: "Aplazado",
  sin_votacion: "Sin votación"
};

export { CATEGORIAS as C, RESULTADO_LABEL as R, TIPO_LABEL as T, getPuntosPleno as a, getVotacionesPunto as b, getPlenosFiltrados as c, getMunicipio as d, getPlenosByMunicipio as e, getMunicipios as f, getPleno as g, supabase as s };
