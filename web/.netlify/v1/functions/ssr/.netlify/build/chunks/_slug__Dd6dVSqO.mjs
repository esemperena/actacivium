import { c as createComponent } from './astro-component_7ATDtAtY.mjs';
import 'piccolore';
import { i as renderComponent, r as renderTemplate, m as maybeRenderHead, f as addAttribute, j as Fragment } from './ssr-function_DV3Szxnz.mjs';
import { $ as $$Base } from './Base_Bzt3yfpW.mjs';
import { $ as $$PlenoCard } from './PlenoCard_RiQqZPId.mjs';
import { d as getMunicipio, e as getPlenosByMunicipio, s as supabase, C as CATEGORIAS } from './supabase_Cxhp8T3W.mjs';

const prerender = false;
const $$slug = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$slug;
  const { slug } = Astro2.params;
  const municipio = await getMunicipio(slug);
  if (!municipio) return Astro2.redirect("/");
  const page = Number(Astro2.url.searchParams.get("page") ?? 1);
  const { data: plenos, count } = await getPlenosByMunicipio(municipio.id, page);
  const totalPages = Math.ceil((count ?? 0) / 20);
  let totalAprobados = 0, totalRechazados = 0, totalPuntos = 0;
  try {
    const ids = plenos.map((p) => p.id);
    if (ids.length > 0) {
      const { data: pts } = await supabase.from("puntos").select("resultado").in("pleno_id", ids);
      totalPuntos = pts?.length ?? 0;
      totalAprobados = pts?.filter((p) => p.resultado === "aprobado").length ?? 0;
      totalRechazados = pts?.filter((p) => p.resultado === "rechazado").length ?? 0;
    }
  } catch {
  }
  let catStats = [];
  try {
    const ids = plenos.map((p) => p.id);
    if (ids.length > 0) {
      const { data } = await supabase.from("puntos").select("categoria").in("pleno_id", ids).neq("categoria", "otro");
      const counts = {};
      for (const row of data ?? []) {
        counts[row.categoria] = (counts[row.categoria] ?? 0) + 1;
      }
      catStats = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([categoria, total]) => ({ categoria, total }));
    }
  } catch {
  }
  const ultimaFecha = plenos[0]?.fecha ? (/* @__PURE__ */ new Date(plenos[0].fecha + "T12:00:00")).toLocaleDateString("es-ES", {
    day: "numeric",
    month: "long",
    year: "numeric"
  }) : null;
  const primerFecha = plenos.length > 0 ? (/* @__PURE__ */ new Date(plenos[plenos.length - 1].fecha + "T12:00:00")).toLocaleDateString("es-ES", {
    month: "long",
    year: "numeric"
  }) : null;
  return renderTemplate`${renderComponent($$result, "Base", $$Base, { "title": `${municipio.nombre} · Plenos Municipales · Acta Civium`, "description": `Plenos municipales del Ayuntamiento de ${municipio.nombre}. ${count} actas analizadas desde una perspectiva ciudadana.` }, { "default": async ($$result2) => renderTemplate`  ${maybeRenderHead()}<nav class="flex items-center gap-2 text-xs text-[var(--color-ink-muted)] mb-8"> <a href="/" class="hover:underline">← Inicio</a> <span>/</span> <span class="text-[var(--color-ink)] font-medium">${municipio.nombre}</span> </nav>  <header class="mb-10 pb-8 border-b-2 border-[var(--color-ink)]"> <!-- Franja de color del gobierno --> <div class="h-1.5 w-12 mb-6 rounded-sm"${addAttribute(`background: ${municipio.color_gobierno ?? "#1a3a2a"}`, "style")}></div> <div class="flex flex-wrap items-start justify-between gap-6"> <div> <p class="text-xs font-bold uppercase tracking-widest text-[var(--color-ink-muted)] mb-2"> ${municipio.provincia} · ${municipio.comunidad} </p> <h1 class="headline-xl mb-1"> ${municipio.nombre} ${municipio.nombre_alt && municipio.nombre_alt !== municipio.nombre && renderTemplate`<span class="font-normal text-[var(--color-ink-muted)]"> · ${municipio.nombre_alt}</span>`} </h1> ${ultimaFecha && renderTemplate`<p class="text-sm text-[var(--color-ink-muted)] mt-2">
Cobertura desde ${primerFecha} · Último pleno: ${ultimaFecha} </p>`} </div> <a href="/newsletter" class="shrink-0 bg-[var(--color-accent)] text-white text-sm font-bold px-5 py-3 hover:bg-[#0f2218] transition-colors">
Recibir newsletter →
</a> </div> </header>  <section class="mb-10"> <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 border border-[var(--color-border)] divide-x divide-y sm:divide-y-0 divide-[var(--color-border)]"> ${[
    { label: "Actas analizadas", value: count, sub: "" },
    { label: "Puntos tratados", value: totalPuntos, sub: "" },
    { label: "Aprobados", value: totalAprobados, sub: "", cls: "text-[#1b5e20]" },
    { label: "Rechazados", value: totalRechazados, sub: "", cls: "text-[#c41a1a]" },
    { label: "Concejales", value: municipio.n_concejales ?? "—", sub: "" },
    {
      label: "Gobierno",
      value: municipio.partido_gobierno ?? "—",
      sub: municipio.alcalde ? municipio.alcalde.split(" ").slice(-2).join(" ") : "",
      cls: "text-base leading-tight"
    }
  ].map(({ label, value, sub, cls }) => renderTemplate`<div class="text-center py-5 px-2 bg-white"> <p${addAttribute(["font-serif font-bold", cls ?? "text-3xl"], "class:list")}>${value}</p> ${sub && renderTemplate`<p class="text-[10px] text-[var(--color-ink-muted)] mt-0.5">${sub}</p>`} <p class="text-[10px] uppercase tracking-widest text-[var(--color-ink-muted)] mt-1">${label}</p> </div>`)} </div> </section> <div class="grid lg:grid-cols-[1fr_260px] gap-10"> <!-- ── LISTA DE ACTAS ───────────────────────────────────────────────── --> <div> <div class="section-rule mb-6"> <span class="text-xs font-bold uppercase tracking-widest">
Actas de plenos · ${count} ${(count ?? 0) === 1 ? "sesión" : "sesiones"} </span> </div> ${plenos.length === 0 ? renderTemplate`<p class="text-[var(--color-ink-muted)] text-sm py-8 text-center border border-dashed border-[var(--color-border)]">
No hay actas procesadas todavía.
</p>` : renderTemplate`${renderComponent($$result2, "Fragment", Fragment, {}, { "default": async ($$result3) => renderTemplate` <div> ${plenos.map((p, i) => renderTemplate`${renderComponent($$result3, "PlenoCard", $$PlenoCard, { "pleno": p, "featured": i === 0 && page === 1 })}`)} </div> ${totalPages > 1 && renderTemplate`<nav class="flex justify-between items-center mt-8 pt-4 border-t border-[var(--color-border)]"> ${page > 1 ? renderTemplate`<a${addAttribute(`/ciudad/${slug}?page=${page - 1}`, "href")} class="text-sm font-semibold hover:underline">← Más recientes</a>` : renderTemplate`<span></span>`} <span class="text-xs text-[var(--color-ink-muted)]">Página ${page} de ${totalPages}</span> ${page < totalPages ? renderTemplate`<a${addAttribute(`/ciudad/${slug}?page=${page + 1}`, "href")} class="text-sm font-semibold hover:underline">Anteriores →</a>` : renderTemplate`<span></span>`} </nav>`}` })}`} </div> <!-- ── SIDEBAR ──────────────────────────────────────────────────────── --> <aside class="space-y-8"> <!-- Ficha del municipio --> <div class="border border-[var(--color-border)] p-4 text-sm space-y-3"> <div class="section-rule"> <span class="text-xs font-bold uppercase tracking-widest">Ficha</span> </div> <dl class="space-y-2.5"> ${municipio.alcalde && renderTemplate`<div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)]">Alcalde/sa</dt> <dd class="font-medium mt-0.5">${municipio.alcalde}</dd> </div>`} ${municipio.partido_gobierno && renderTemplate`<div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)]">Partido de gobierno</dt> <dd class="font-medium mt-0.5 flex items-center gap-2"> <span class="w-2 h-2 rounded-full inline-block"${addAttribute(`background: ${municipio.color_gobierno ?? "#888"}`, "style")}></span> ${municipio.partido_gobierno} </dd> </div>`} ${municipio.n_concejales && renderTemplate`<div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)]">Concejales</dt> <dd class="font-medium mt-0.5">${municipio.n_concejales}</dd> </div>`} ${municipio.poblacion && renderTemplate`<div> <dt class="text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)]">Población</dt> <dd class="font-medium mt-0.5">${municipio.poblacion.toLocaleString("es-ES")} hab.</dd> </div>`} ${municipio.web_oficial && renderTemplate`<div class="pt-1"> <a${addAttribute(municipio.web_oficial, "href")} target="_blank" rel="noopener noreferrer" class="text-xs font-semibold text-[var(--color-accent)] hover:underline">
Web oficial del Ayuntamiento →
</a> </div>`} </dl> </div> <!-- Temas más tratados --> ${catStats.length > 0 && renderTemplate`<div> <div class="section-rule mb-4"> <span class="text-xs font-bold uppercase tracking-widest">Temas más tratados</span> </div> <div class="space-y-2"> ${catStats.map(({ categoria, total }) => renderTemplate`<a${addAttribute(`/temas/${categoria}`, "href")} class="flex items-center justify-between py-1.5 border-b border-[var(--color-border)] last:border-0 hover:text-[var(--color-accent)] transition-colors group"> <span${addAttribute(["badge", `badge-${categoria}`], "class:list")}> ${CATEGORIAS[categoria] ?? categoria} </span> <span class="text-xs text-[var(--color-ink-muted)] group-hover:text-[var(--color-accent)]"> ${total} ${total === 1 ? "punto" : "puntos"} </span> </a>`)} </div> </div>`} </aside> </div> ` })}`;
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/ciudad/[slug].astro", void 0);

const $$file = "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/ciudad/[slug].astro";
const $$url = "/ciudad/[slug]";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$slug,
  file: $$file,
  prerender,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
