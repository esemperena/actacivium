import { c as createComponent } from './astro-component_7ATDtAtY.mjs';
import 'piccolore';
import { i as renderComponent, r as renderTemplate, m as maybeRenderHead, f as addAttribute } from './ssr-function_DV3Szxnz.mjs';
import { $ as $$Base } from './Base_Bzt3yfpW.mjs';
import { g as getPleno, a as getPuntosPleno, s as supabase, b as getVotacionesPunto, C as CATEGORIAS, R as RESULTADO_LABEL, T as TIPO_LABEL } from './supabase_Cxhp8T3W.mjs';

const prerender = false;
const $$id = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$id;
  const { id } = Astro2.params;
  const pleno = await getPleno(id);
  if (!pleno) return Astro2.redirect("/actas");
  const [puntos, { data: meta }] = await Promise.all([
    getPuntosPleno(id),
    supabase.from("plenos").select("url_pdf_original, n_asistentes, n_ausentes, alcalde_nombre, secretaria_nombre, hora_inicio, hora_fin, texto_completo, municipio_id").eq("id", id).single()
  ]);
  const votacionesPorPunto = {};
  for (const p of puntos) {
    if (p.resultado !== "sin_votacion" && p.resultado !== "enterado") {
      const v = await getVotacionesPunto(p.id);
      if (v.length > 0) votacionesPorPunto[p.id] = v;
    }
  }
  let municipioSlug = "";
  let municipioNombre = pleno.municipio ?? "San Sebastián";
  if (meta?.municipio_id) {
    try {
      const { data: muni } = await supabase.from("municipios").select("slug, nombre").eq("id", meta.municipio_id).single();
      municipioSlug = muni?.slug ?? "";
      municipioNombre = muni?.nombre ?? municipioNombre;
    } catch {
    }
  }
  const fecha = /* @__PURE__ */ new Date(pleno.fecha + "T12:00:00");
  const fechaLarga = fecha.toLocaleDateString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric"
  });
  const fechaCorta = fecha.toLocaleDateString("es-ES", {
    day: "numeric",
    month: "short",
    year: "numeric"
  });
  const categorias = [...new Set(
    puntos.map((p) => p.categoria).filter((c) => c && c !== "otro")
  )];
  const puntosUrgentes = puntos.filter((p) => p.es_urgencia);
  const puntosResolutivos = puntos.filter((p) => !p.es_urgencia && !["dar_cuenta", "otro"].includes(p.tipo));
  const puntosInformativos = puntos.filter((p) => !p.es_urgencia && ["dar_cuenta", "otro"].includes(p.tipo));
  const textoPreview = (meta?.texto_completo ?? "").replace(/AKTA \d+ ACTA \d+\n[^\n]+\n/g, "").slice(0, 3e3).replace(/\n{3,}/g, "\n\n").trim();
  const RESULTADO_COLOR = {
    aprobado: "text-[#1b5e20] font-semibold",
    rechazado: "text-[#c41a1a] font-semibold",
    enterado: "text-[var(--color-ink-muted)]",
    retirado: "text-[#92400e] font-semibold",
    aplazado: "text-[#92400e]",
    sin_votacion: "text-[var(--color-ink-muted)]"
  };
  return renderTemplate`${renderComponent($$result, "Base", $$Base, { "title": `Pleno nº ${pleno.numero_acta} · ${fechaCorta} · ${municipioNombre}`, "description": `Pleno municipal de ${municipioNombre} nº ${pleno.numero_acta}, celebrado el ${fechaLarga}. ${puntos.length} puntos del orden del día.` }, { "default": async ($$result2) => renderTemplate`  ${maybeRenderHead()}<nav class="flex items-center gap-2 text-xs text-[var(--color-ink-muted)] mb-6 flex-wrap"> <a href="/" class="hover:underline">Inicio</a> <span>/</span> ${municipioSlug ? renderTemplate`<a${addAttribute(`/ciudad/${municipioSlug}`, "href")} class="hover:underline">${municipioNombre}</a>` : renderTemplate`<span>${municipioNombre}</span>`} <span>/</span> <span class="text-[var(--color-ink)] font-medium">Pleno nº ${pleno.numero_acta}</span> </nav>  <header class="mb-8 pb-8 border-b-2 border-[var(--color-ink)]"> <div class="flex flex-wrap items-center gap-3 mb-3"> <span class="text-xs font-bold uppercase tracking-widest text-[var(--color-ink-muted)]"> ${municipioNombre} · Pleno nº ${pleno.numero_acta} </span> <span${addAttribute([
    "badge",
    pleno.tipo_sesion === "extraordinaria" ? "bg-amber-100 text-amber-800" : "bg-[var(--color-accent-light)] text-[var(--color-accent)]"
  ], "class:list")}>
Sesión ${pleno.tipo_sesion} </span> ${meta?.url_pdf_original && renderTemplate`<a${addAttribute(meta.url_pdf_original, "href")} target="_blank" rel="noopener noreferrer" class="ml-auto text-xs font-semibold border border-[var(--color-ink)] px-3 py-1.5 hover:bg-[var(--color-ink)] hover:text-white transition-colors">
PDF original ↗
</a>`} </div> <h1 class="headline-xl mb-4" style="text-transform: capitalize;">${fechaLarga}</h1> ${pleno.resumen_ia && renderTemplate`<p class="text-base text-[var(--color-ink-muted)] leading-relaxed border-l-4 border-[var(--color-accent)] pl-4 max-w-2xl"> ${pleno.resumen_ia} </p>`} </header>  <section class="mb-8"> <div class="grid grid-cols-3 sm:grid-cols-6 border border-[var(--color-border)] divide-x divide-y sm:divide-y-0 divide-[var(--color-border)]"> ${[
    { label: "Puntos", value: pleno.total_puntos, cls: "" },
    { label: "Aprobados", value: pleno.aprobados, cls: "text-[#1b5e20]" },
    { label: "Rechazados", value: pleno.rechazados, cls: "text-[#c41a1a]" },
    { label: "Unanimidad", value: pleno.unanimes, cls: "" },
    { label: "Concejales", value: meta?.n_asistentes ?? "—", cls: "" },
    { label: "Ausentes", value: meta?.n_ausentes ?? 0, cls: "text-[var(--color-ink-muted)]" }
  ].map(({ label, value, cls }) => renderTemplate`<div class="text-center py-5 px-2 bg-white"> <p${addAttribute(["font-serif font-bold text-3xl", cls], "class:list")}>${value}</p> <p class="text-[10px] uppercase tracking-widest text-[var(--color-ink-muted)] mt-1">${label}</p> </div>`)} </div> </section>  <section class="mb-10"> <div class="section-rule mb-4"> <span class="text-xs font-bold uppercase tracking-widest">Ficha del pleno</span> </div> <dl class="grid sm:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-4 text-sm"> <div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] mb-0.5">Fecha</dt> <dd class="font-medium" style="text-transform: capitalize;">${fechaLarga}</dd> </div> ${meta?.hora_inicio && renderTemplate`<div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] mb-0.5">Hora de inicio</dt> <dd class="font-medium">${String(meta.hora_inicio).slice(0, 5)} h</dd> </div>`} ${meta?.alcalde_nombre && renderTemplate`<div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] mb-0.5">Preside</dt> <dd class="font-medium">${meta.alcalde_nombre}</dd> </div>`} ${meta?.secretaria_nombre && renderTemplate`<div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] mb-0.5">Secretaría</dt> <dd class="font-medium">${meta.secretaria_nombre}</dd> </div>`} <div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] mb-0.5">Tipo de sesión</dt> <dd class="font-medium" style="text-transform: capitalize;">${pleno.tipo_sesion}</dd> </div> ${(meta?.n_asistentes ?? 0) > 0 && renderTemplate`<div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] mb-0.5">Asistencia</dt> <dd class="font-medium"> ${meta.n_asistentes} concejales
${(meta?.n_ausentes ?? 0) > 0 && renderTemplate`<span class="font-normal text-[var(--color-ink-muted)]"> · ${meta.n_ausentes} ausentes</span>`} </dd> </div>`} ${categorias.length > 0 && renderTemplate`<div class="sm:col-span-2"> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] mb-2">Temas tratados</dt> <dd class="flex flex-wrap gap-2"> ${categorias.map((cat) => renderTemplate`<a${addAttribute(`/temas/${cat}`, "href")}${addAttribute(["badge hover:opacity-75 transition-opacity", `badge-${cat}`], "class:list")}> ${CATEGORIAS[cat] ?? cat} </a>`)} </dd> </div>`} </dl> </section>  <section class="mb-10"> <div class="section-rule mb-6"> <span class="text-xs font-bold uppercase tracking-widest">
Orden del día — ${puntos.length} ${puntos.length === 1 ? "punto" : "puntos"} </span> </div> ${puntos.length === 0 ? renderTemplate`<p class="text-[var(--color-ink-muted)] text-sm py-12 text-center border border-dashed border-[var(--color-border)]">
Los puntos del orden del día se están procesando.
</p>` : renderTemplate`<div class="space-y-3"> <!-- Urgencias primero --> ${puntosUrgentes.map((p) => {
    const votos = votacionesPorPunto[p.id] ?? [];
    return renderTemplate`<div class="border border-amber-200 bg-amber-50 p-5"> <div class="flex flex-wrap items-start gap-x-4 gap-y-2"> <span class="font-mono text-xs font-bold text-amber-700 shrink-0 mt-0.5">URG</span> <div class="flex-1 min-w-0"> <div class="flex flex-wrap gap-2 mb-2"> <span class="badge bg-amber-100 text-amber-800">Urgencia</span> ${p.categoria !== "otro" && renderTemplate`<span${addAttribute(["badge", `badge-${p.categoria}`], "class:list")}>${CATEGORIAS[p.categoria]}</span>`} </div> <p class="font-serif font-semibold text-base leading-snug">${p.titulo}</p> ${p.resumen_ia && renderTemplate`<p class="text-sm text-[var(--color-ink-muted)] mt-2">${p.resumen_ia}</p>`} ${votos.length > 0 && renderTemplate`${renderComponent($$result2, "VotsTable", VotsTable, { "votos": votos })}`} </div> <span${addAttribute(["text-xs shrink-0 mt-0.5 font-semibold", RESULTADO_COLOR[p.resultado] ?? ""], "class:list")}> ${RESULTADO_LABEL[p.resultado] ?? p.resultado} ${p.unanimidad && renderTemplate`<span class="font-normal text-[var(--color-ink-muted)]"> · unánime</span>`} </span> </div> </div>`;
  })} <!-- Puntos resolutivos --> ${puntosResolutivos.length > 0 && renderTemplate`<div> <p class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-ink-muted)] py-2 mt-2">
— Parte resolutiva
</p> ${puntosResolutivos.map((p) => {
    const votos = votacionesPorPunto[p.id] ?? [];
    return renderTemplate`<div${addAttribute([
      "border border-[var(--color-border)] bg-white p-5 mb-3",
      (p.relevancia_social ?? 0) >= 4 && "border-l-4 border-l-[var(--color-accent)]"
    ], "class:list")}> <div class="flex flex-wrap items-start gap-x-4 gap-y-2"> <span class="font-mono text-sm font-bold text-[var(--color-ink-muted)] w-6 shrink-0 mt-0.5"> ${p.numero}.
</span> <div class="flex-1 min-w-0"> <div class="flex flex-wrap gap-2 mb-2"> ${p.categoria !== "otro" && renderTemplate`<span${addAttribute(["badge", `badge-${p.categoria}`], "class:list")}>${CATEGORIAS[p.categoria]}</span>`} <span class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] border border-[var(--color-border)] px-2 py-0.5"> ${TIPO_LABEL[p.tipo] ?? p.tipo} </span> ${(p.relevancia_social ?? 0) >= 4 && renderTemplate`<span class="flex items-center gap-1 text-[10px] text-[var(--color-accent)]"> ${Array.from({ length: p.relevancia_social ?? 0 }).map(() => renderTemplate`<span class="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)] inline-block"></span>`)} <span class="ml-0.5 uppercase tracking-wide">Alta relevancia</span> </span>`} </div> <p class="font-serif font-semibold text-base leading-snug">${p.titulo}</p> ${p.resumen_ia && renderTemplate`<p class="text-sm text-[var(--color-ink-muted)] mt-2 leading-relaxed">${p.resumen_ia}</p>`} ${votos.length > 0 && renderTemplate`<div class="mt-3 pt-3 border-t border-[var(--color-border)]"> <p class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-ink-muted)] mb-2">
Votación por partido
</p> <div class="flex flex-wrap gap-2"> ${votos.map((v) => renderTemplate`<div class="flex items-center gap-1.5 text-xs border border-[var(--color-border)] px-2 py-1 bg-gray-50"> <span class="w-2 h-2 rounded-full shrink-0"${addAttribute(`background:${v.color_hex}`, "style")}></span> <span class="font-semibold">${v.siglas}</span> <span class="text-[var(--color-ink-muted)]"> ${v.votos_favor > 0 && renderTemplate`<span class="text-[#1b5e20]">${v.votos_favor}✓</span>`} ${v.votos_contra > 0 && renderTemplate`<span class="text-[#c41a1a] ml-1">${v.votos_contra}✗</span>`} ${v.abstenciones > 0 && renderTemplate`<span class="ml-1">${v.abstenciones}~</span>`} </span> </div>`)} </div> </div>`} </div> <div class="shrink-0 mt-0.5 text-right"> <span${addAttribute(["text-xs", RESULTADO_COLOR[p.resultado] ?? ""], "class:list")}> ${RESULTADO_LABEL[p.resultado] ?? p.resultado} </span> ${p.unanimidad === true && renderTemplate`<p class="text-[10px] text-[var(--color-ink-muted)]">unanimidad</p>`} ${p.unanimidad === false && renderTemplate`<p class="text-[10px] text-[var(--color-ink-muted)]">mayoría</p>`} </div> </div> </div>`;
  })} </div>`} <!-- Puntos informativos (dar cuenta) en collapsible --> ${puntosInformativos.length > 0 && renderTemplate`<details class="group mt-4"> <summary class="section-rule mb-0 cursor-pointer list-none flex items-center justify-between py-2"> <span class="text-xs font-bold uppercase tracking-widest">
Informes y comunicaciones (${puntosInformativos.length})
</span> <span class="text-xs text-[var(--color-ink-muted)] group-open:hidden">Mostrar ↓</span> <span class="text-xs text-[var(--color-ink-muted)] hidden group-open:block">Cerrar ↑</span> </summary> <div class="mt-3 space-y-2"> ${puntosInformativos.map((p) => renderTemplate`<div class="border border-[var(--color-border)] bg-white px-5 py-3 flex items-start gap-4"> <span class="font-mono text-xs text-[var(--color-ink-muted)] shrink-0 mt-0.5 w-5">${p.numero}.</span> <div class="flex-1 min-w-0"> <p class="text-sm font-medium leading-snug">${p.titulo}</p> ${p.categoria && p.categoria !== "otro" && renderTemplate`<span${addAttribute(["badge mt-1.5", `badge-${p.categoria}`], "class:list")}>${CATEGORIAS[p.categoria]}</span>`} </div> <span class="text-xs text-[var(--color-ink-muted)] shrink-0">Enterado</span> </div>`)} </div> </details>`} </div>`} </section>  ${textoPreview && renderTemplate`<section class="mb-10"> <details class="group"> <summary class="section-rule mb-0 cursor-pointer list-none flex items-center justify-between py-2"> <span class="text-xs font-bold uppercase tracking-widest">Extracto del texto oficial</span> <span class="text-xs text-[var(--color-ink-muted)] group-open:hidden">Mostrar ↓</span> <span class="text-xs text-[var(--color-ink-muted)] hidden group-open:block">Cerrar ↑</span> </summary> <div class="mt-4 p-5 bg-white border border-[var(--color-border)] text-xs leading-relaxed text-[var(--color-ink-muted)] whitespace-pre-wrap font-mono max-h-80 overflow-y-auto"> ${textoPreview}…
</div> ${meta?.url_pdf_original && renderTemplate`<p class="mt-3 text-center"> <a${addAttribute(meta.url_pdf_original, "href")} target="_blank" rel="noopener noreferrer" class="text-xs font-semibold text-[var(--color-accent)] hover:underline">
Ver acta completa en PDF →
</a> </p>`} </details> </section>`} <div class="border-t border-[var(--color-border)] pt-6 flex justify-between items-center"> ${municipioSlug ? renderTemplate`<a${addAttribute(`/ciudad/${municipioSlug}`, "href")} class="text-sm font-semibold hover:underline">← Todas las actas</a>` : renderTemplate`<a href="/actas" class="text-sm font-semibold hover:underline">← Todas las actas</a>`} <a href="/newsletter" class="text-sm font-semibold text-[var(--color-accent)] hover:underline">
Suscribirse a la newsletter →
</a> </div> ` })}`;
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/acta/[id].astro", void 0);

const $$file = "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/acta/[id].astro";
const $$url = "/acta/[id]";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$id,
  file: $$file,
  prerender,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
