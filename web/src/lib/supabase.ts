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
  texto_completo: string | null;
  relevancia_social: number | null;
  es_urgencia: boolean;
  grupo_proponente_id?: string | null;
}

export interface Votacion {
  partido: string;
  siglas: string;
  color_hex: string;
  n_concejales: number | null;
  votos_favor: number;
  votos_contra: number;
  abstenciones: number;
}

export interface AsistenciaPartido {
  sigla: string;
  color: string;
  presentes: number;
  total: number;
}

export interface CityDashboardData {
  summary: {
    totalPlenos: number;
    totalPuntos: number;
    totalAprobados: number;
    totalRechazados: number;
    totalUnanimes: number;
    avgPuntos: number;
    attendanceAvg: number | null;
    firstDate: string | null;
    lastDate: string | null;
  };
  composicion: Array<{
    sigla: string;
    color: string;
    concejales: number;
  }>;
  categoryStats: Array<{
    categoria: string;
    label: string;
    total: number;
    share: number;
  }>;
  resultStats: Array<{
    resultado: string;
    label: string;
    total: number;
    share: number;
  }>;
  alignments: Array<{
    partyA: string;
    partyB: string;
    colorA: string;
    colorB: string;
    comparedPoints: number;
    sameVotes: number;
    sameVoteShare: number;
  }>;
  alignmentByCategory: Array<{
    categoria: string;
    label: string;
    totalComparisons: number;
    pairs: Array<{
      partyA: string;
      partyB: string;
      colorA: string;
      colorB: string;
      comparedPoints: number;
      sameVotes: number;
      sameVoteShare: number;
    }>;
  }>;
  lowConsensusCategories: Array<{
    categoria: string;
    label: string;
    votedPoints: number;
    unanimousPoints: number;
    conflictShare: number;
  }>;
  proposalSummary: {
    gobierno: { total: number; aprobadas: number; rechazadas: number; };
    oposicion: { total: number; aprobadas: number; rechazadas: number; };
  };
  featuredPoints: Array<{
    plenoId: string;
    numeroActa: number;
    fecha: string;
    titulo: string;
    categoria: string;
    relevancia: number;
    resultado: string;
    proponente: string | null;
    bloque: "gobierno" | "oposicion" | "sin_clasificar";
  }>;
  timeline: Array<{
    id: string;
    numero_acta: number;
    fecha: string;
    tipo_sesion: string;
    total_puntos: number;
    aprobados: number;
    rechazados: number;
    unanimes: number;
    n_asistentes: number | null;
  }>;
  highlights: Array<{
    plenoId: string;
    numeroActa: number;
    fecha: string;
    titulo: string;
    categoria: string;
    resultado: string;
  }>;
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

function partyMatchesGovernment(sigla: string, partidoGobierno: string | null | undefined) {
  if (!sigla || !partidoGobierno) return false;
  const left = sigla.toUpperCase().trim();
  const right = partidoGobierno.toUpperCase().trim();
  return left === right || left.includes(right) || right.includes(left);
}

export async function getCityDashboard(
  municipioId: string,
  partidoGobierno?: string | null
): Promise<CityDashboardData> {
  const empty: CityDashboardData = {
    summary: {
      totalPlenos: 0,
      totalPuntos: 0,
      totalAprobados: 0,
      totalRechazados: 0,
      totalUnanimes: 0,
      avgPuntos: 0,
      attendanceAvg: null,
      firstDate: null,
      lastDate: null,
    },
    composicion: [],
    categoryStats: [],
    resultStats: [],
    alignments: [],
    alignmentByCategory: [],
    lowConsensusCategories: [],
    proposalSummary: {
      gobierno: { total: 0, aprobadas: 0, rechazadas: 0 },
      oposicion: { total: 0, aprobadas: 0, rechazadas: 0 },
    },
    featuredPoints: [],
    timeline: [],
    highlights: [],
  };

  try {
    const [plenosRes, partidosRes] = await Promise.all([
      supabase
        .from("v_plenos")
        .select("id, numero_acta, fecha, tipo_sesion, total_puntos, aprobados, rechazados, unanimes, n_asistentes")
        .eq("municipio_id", municipioId)
        .eq("estado", "procesado")
        .order("fecha", { ascending: false }),
      supabase
        .from("partidos")
        .select("siglas, color_hex, n_concejales")
        .eq("municipio_id", municipioId)
        .eq("activo", true)
        .order("n_concejales", { ascending: false }),
    ]);

    const plenos = plenosRes.data ?? [];
    const composicion = (partidosRes.data ?? [])
      .filter((row) => (row.n_concejales ?? 0) > 0)
      .map((row) => ({
        sigla: row.siglas,
        color: row.color_hex ?? "#888888",
        concejales: row.n_concejales ?? 0,
      }));

    if (plenos.length === 0) {
      return { ...empty, composicion };
    }

    const governmentSiglas = new Set(
      composicion
        .filter((row) => partyMatchesGovernment(row.sigla, partidoGobierno))
        .map((row) => row.sigla)
    );

    const plenoIds = plenos.map((pleno) => pleno.id);
    const { data: puntosData } = await supabase
      .from("puntos")
      .select("id, pleno_id, titulo, categoria, resultado, tipo, unanimidad, relevancia_social, grupo_proponente_id, partidos:grupo_proponente_id(siglas)")
      .in("pleno_id", plenoIds);
    const { data: votacionesData } = await supabase
      .from("votaciones")
      .select("punto_id, votos_favor, votos_contra, abstenciones, partidos(siglas, color_hex)")
      .in("punto_id", (puntosData ?? []).map((p) => p.id).filter(Boolean));

    const puntos = puntosData ?? [];
    const votaciones = votacionesData ?? [];
    const totalPuntos = puntos.length;
    const totalPlenos = plenos.length;
    const totalAprobados = puntos.filter((p) => p.resultado === "aprobado").length;
    const totalRechazados = puntos.filter((p) => p.resultado === "rechazado").length;
    const totalUnanimes = puntos.filter((p) => p.unanimidad === true).length;
    const attendance = plenos
      .map((p) => p.n_asistentes)
      .filter((value): value is number => typeof value === "number");

    const categoryCounts: Record<string, number> = {};
    const pointCategory = new Map<string, string>();
    for (const punto of puntos) {
      const categoria = punto.categoria ?? "otro";
      categoryCounts[categoria] = (categoryCounts[categoria] ?? 0) + 1;
      pointCategory.set(punto.id, categoria);
    }

    const categoryStats = Object.entries(categoryCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([categoria, total]) => ({
        categoria,
        label: CATEGORIAS[categoria] ?? categoria,
        total,
        share: totalPuntos > 0 ? total / totalPuntos : 0,
      }));

    const resultEntries = [
      ["aprobado", "Aprobados"],
      ["rechazado", "Rechazados"],
      ["enterado", "Enterados"],
      ["sin_votacion", "Sin votacion"],
      ["aplazado", "Aplazados"],
      ["retirado", "Retirados"],
    ] as const;

    const resultStats = resultEntries
      .map(([resultado, label]) => {
        const total = puntos.filter((p) => p.resultado === resultado).length;
        return {
          resultado,
          label,
          total,
          share: totalPuntos > 0 ? total / totalPuntos : 0,
        };
      })
      .filter((row) => row.total > 0);

    const stanceByPoint = new Map<string, Array<{ sigla: string; color: string; stance: string }>>();
    for (const row of votaciones as any[]) {
      const sigla = row.partidos?.siglas;
      if (!sigla) continue;
      const stance =
        row.votos_favor > 0 ? "favor" :
        row.votos_contra > 0 ? "contra" :
        row.abstenciones > 0 ? "abstencion" :
        null;
      if (!stance) continue;
      const color = row.partidos?.color_hex ?? "#888888";
      const list = stanceByPoint.get(row.punto_id) ?? [];
      list.push({ sigla, color, stance });
      stanceByPoint.set(row.punto_id, list);
    }

    const pairStats = new Map<string, {
      partyA: string;
      partyB: string;
      colorA: string;
      colorB: string;
      comparedPoints: number;
      sameVotes: number;
    }>();
    const pairStatsByCategory = new Map<string, Map<string, {
      partyA: string;
      partyB: string;
      colorA: string;
      colorB: string;
      comparedPoints: number;
      sameVotes: number;
    }>>();

    for (const [pointId, stances] of stanceByPoint.entries()) {
      const categoria = pointCategory.get(pointId) ?? "otro";
      for (let i = 0; i < stances.length; i += 1) {
        for (let j = i + 1; j < stances.length; j += 1) {
          const left = stances[i];
          const right = stances[j];
          const [first, second] = [left, right].sort((a, b) => a.sigla.localeCompare(b.sigla));
          const key = `${first.sigla}__${second.sigla}`;
          const current = pairStats.get(key) ?? {
            partyA: first.sigla,
            partyB: second.sigla,
            colorA: first.color,
            colorB: second.color,
            comparedPoints: 0,
            sameVotes: 0,
          };
          current.comparedPoints += 1;
          if (first.stance === second.stance) {
            current.sameVotes += 1;
          }
          pairStats.set(key, current);

          const categoryPairs = pairStatsByCategory.get(categoria) ?? new Map<string, {
            partyA: string;
            partyB: string;
            colorA: string;
            colorB: string;
            comparedPoints: number;
            sameVotes: number;
          }>();
          const categoryCurrent = categoryPairs.get(key) ?? {
            partyA: first.sigla,
            partyB: second.sigla,
            colorA: first.color,
            colorB: second.color,
            comparedPoints: 0,
            sameVotes: 0,
          };
          categoryCurrent.comparedPoints += 1;
          if (first.stance === second.stance) {
            categoryCurrent.sameVotes += 1;
          }
          categoryPairs.set(key, categoryCurrent);
          pairStatsByCategory.set(categoria, categoryPairs);
        }
      }
    }

    const alignments = Array.from(pairStats.values())
      .filter((item) => item.comparedPoints >= 2)
      .map((item) => ({
        ...item,
        sameVoteShare: item.comparedPoints > 0 ? item.sameVotes / item.comparedPoints : 0,
      }))
      .sort((a, b) =>
        b.sameVoteShare - a.sameVoteShare ||
        b.comparedPoints - a.comparedPoints ||
        a.partyA.localeCompare(b.partyA)
      );

    const alignmentByCategory = Array.from(pairStatsByCategory.entries())
      .map(([categoria, pairs]) => {
        const normalizedPairs = Array.from(pairs.values())
          .map((item) => ({
            ...item,
            sameVoteShare: item.comparedPoints > 0 ? item.sameVotes / item.comparedPoints : 0,
          }))
          .sort((a, b) =>
            b.comparedPoints - a.comparedPoints ||
            b.sameVoteShare - a.sameVoteShare ||
            a.partyA.localeCompare(b.partyA)
          );

        return {
          categoria,
          label: CATEGORIAS[categoria] ?? categoria,
          totalComparisons: normalizedPairs.reduce((sum, item) => sum + item.comparedPoints, 0),
          pairs: normalizedPairs,
        };
      })
      .filter((item) => item.pairs.length > 0)
      .sort((a, b) => b.totalComparisons - a.totalComparisons)
      .slice(0, 5);

    const lowConsensusMap = new Map<string, { votedPoints: number; unanimousPoints: number }>();
    for (const punto of puntos) {
      if (!stanceByPoint.has(punto.id)) continue;
      const categoria = punto.categoria ?? "otro";
      const current = lowConsensusMap.get(categoria) ?? { votedPoints: 0, unanimousPoints: 0 };
      current.votedPoints += 1;
      if (punto.unanimidad === true) {
        current.unanimousPoints += 1;
      }
      lowConsensusMap.set(categoria, current);
    }

    const lowConsensusCategories = Array.from(lowConsensusMap.entries())
      .map(([categoria, stats]) => ({
        categoria,
        label: CATEGORIAS[categoria] ?? categoria,
        votedPoints: stats.votedPoints,
        unanimousPoints: stats.unanimousPoints,
        conflictShare: stats.votedPoints > 0 ? 1 - (stats.unanimousPoints / stats.votedPoints) : 0,
      }))
      .filter((item) => item.votedPoints > 0)
      .sort((a, b) =>
        b.conflictShare - a.conflictShare ||
        b.votedPoints - a.votedPoints ||
        a.label.localeCompare(b.label)
      )
      .slice(0, 5);

    const proposalSummary = {
      gobierno: { total: 0, aprobadas: 0, rechazadas: 0 },
      oposicion: { total: 0, aprobadas: 0, rechazadas: 0 },
    };

    const featuredPoints = puntos
      .map((punto: any) => {
        const pleno = plenos.find((item) => item.id === punto.pleno_id);
        const proponente = punto.partidos?.siglas ?? null;
        const bloque: "gobierno" | "oposicion" | "sin_clasificar" =
          proponente
            ? (governmentSiglas.has(proponente) ? "gobierno" : "oposicion")
            : "sin_clasificar";

        if (proponente && bloque !== "sin_clasificar") {
          proposalSummary[bloque].total += 1;
          if (punto.resultado === "aprobado") proposalSummary[bloque].aprobadas += 1;
          if (punto.resultado === "rechazado") proposalSummary[bloque].rechazadas += 1;
        }

        return {
          plenoId: punto.pleno_id,
          numeroActa: pleno?.numero_acta ?? 0,
          fecha: pleno?.fecha ?? "",
          titulo: punto.titulo,
          categoria: punto.categoria ?? "otro",
          relevancia: punto.relevancia_social ?? 0,
          resultado: punto.resultado ?? "sin_votacion",
          proponente,
          bloque,
          tipo: punto.tipo ?? "otro",
        };
      })
      .filter((item) => item.fecha)
      .sort((a, b) =>
        b.relevancia - a.relevancia ||
        b.fecha.localeCompare(a.fecha) ||
        a.numeroActa - b.numeroActa
      )
      .slice(0, 4)
      .map(({ plenoId, numeroActa, fecha, titulo, categoria, relevancia, resultado, proponente, bloque }) => ({
        plenoId,
        numeroActa,
        fecha,
        titulo,
        categoria,
        relevancia,
        resultado,
        proponente,
        bloque,
      }));

    const timeline = plenos.map((pleno) => ({
      id: pleno.id,
      numero_acta: pleno.numero_acta,
      fecha: pleno.fecha,
      tipo_sesion: pleno.tipo_sesion,
      total_puntos: pleno.total_puntos,
      aprobados: pleno.aprobados,
      rechazados: pleno.rechazados,
      unanimes: pleno.unanimes,
      n_asistentes: pleno.n_asistentes ?? null,
    }));

    const highlights = puntos
      .map((punto) => {
        const pleno = plenos.find((item) => item.id === punto.pleno_id);
        return {
          plenoId: punto.pleno_id,
          numeroActa: pleno?.numero_acta ?? 0,
          fecha: pleno?.fecha ?? "",
          titulo: punto.titulo,
          categoria: punto.categoria ?? "otro",
          resultado: punto.resultado ?? "sin_votacion",
          tipo: punto.tipo ?? "otro",
        };
      })
      .filter((item) => item.fecha)
      .sort((a, b) => {
        const score = (row: typeof a) => {
          const categoryBonus = row.categoria !== "otro" ? 3 : 0;
          const resultBonus = row.resultado === "rechazado" ? 3 : row.resultado === "aprobado" ? 2 : 0;
          const typeBonus = row.tipo === "mocion" ? 2 : row.tipo === "aprobacion_definitiva" ? 1 : 0;
          return categoryBonus + resultBonus + typeBonus;
        };
        return b.fecha.localeCompare(a.fecha) || score(b) - score(a);
      })
      .slice(0, 5)
      .map(({ plenoId, numeroActa, fecha, titulo, categoria, resultado }) => ({
        plenoId,
        numeroActa,
        fecha,
        titulo,
        categoria,
        resultado,
      }));

    return {
      summary: {
        totalPlenos,
        totalPuntos,
        totalAprobados,
        totalRechazados,
        totalUnanimes,
        avgPuntos: totalPlenos > 0 ? totalPuntos / totalPlenos : 0,
        attendanceAvg: attendance.length
          ? attendance.reduce((sum, value) => sum + value, 0) / attendance.length
          : null,
        firstDate: plenos[plenos.length - 1]?.fecha ?? null,
        lastDate: plenos[0]?.fecha ?? null,
      },
      composicion,
      categoryStats,
      resultStats,
      alignments,
      alignmentByCategory,
      lowConsensusCategories,
      proposalSummary,
      featuredPoints,
      timeline,
      highlights,
    };
  } catch {
    return empty;
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

export async function getAsistenciaPleno(plenoId: string): Promise<AsistenciaPartido[]> {
  // Inferimos asistencia por partido desde los datos de votación:
  // seats = máximo de votos emitidos por el partido en cualquier votación del pleno
  // presentes = moda de los recuentos de votos (votación más frecuente)
  // Si seats > presentes → había ausentes de ese partido
  try {
    const { data: puntos } = await supabase
      .from("puntos")
      .select("id")
      .eq("pleno_id", plenoId);
    const puntoIds = puntos?.map((p: any) => p.id) ?? [];
    if (!puntoIds.length) return [];

    const { data } = await supabase
      .from("votaciones")
      .select("votos_favor, votos_contra, abstenciones, partido_id, partidos(siglas, color_hex, n_concejales)")
      .in("punto_id", puntoIds);
    if (!data?.length) return [];

    const byParty: Record<string, { sigla: string; color: string; n_concejales: number | null; counts: number[] }> = {};
    for (const v of data as any[]) {
      if (!v.partido_id || !v.partidos) continue;
      const total = v.votos_favor + v.votos_contra + v.abstenciones;
      if (!byParty[v.partido_id]) {
        byParty[v.partido_id] = {
          sigla: v.partidos.siglas,
          color: v.partidos.color_hex ?? "#888",
          n_concejales: v.partidos.n_concejales ?? null,
          counts: [],
        };
      }
      byParty[v.partido_id].counts.push(total);
    }

    return Object.values(byParty)
      .map((p) => {
        // Escaños: usar el oficial de BD; si no existe, inferir del máximo de votos
        const seats = p.n_concejales ?? Math.max(...p.counts);
        // Presentes: moda de los recuentos de votaciones con votos emitidos
        const active = p.counts.filter((c) => c > 0);
        const freq: Record<number, number> = {};
        for (const c of active) freq[c] = (freq[c] ?? 0) + 1;
        const presentes = active.length
          ? Number(Object.entries(freq).sort((a, b) => b[1] - a[1])[0][0])
          : seats;
        return { sigla: p.sigla, color: p.color, presentes, total: seats };
      })
      .filter((p) => p.total > 0)
      .sort((a, b) => b.total - a.total);
  } catch {
    return [];
  }
}

export async function getVotacionesPunto(puntoId: string): Promise<Votacion[]> {
  try {
    const { data } = await supabase
      .from("votaciones")
      .select(`votos_favor, votos_contra, abstenciones, partidos ( nombre, siglas, color_hex, n_concejales )`)
      .eq("punto_id", puntoId);
    return (data ?? []).map((v: any) => ({
      partido: v.partidos.nombre,
      siglas: v.partidos.siglas,
      color_hex: v.partidos.color_hex,
      n_concejales: v.partidos.n_concejales ?? null,
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
