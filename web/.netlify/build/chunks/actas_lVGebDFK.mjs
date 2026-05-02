import { c as createComponent } from './astro-component_7ATDtAtY.mjs';
import 'piccolore';
import { i as renderComponent, r as renderTemplate, m as maybeRenderHead, j as Fragment, f as addAttribute } from './ssr-function_DV3Szxnz.mjs';
import { $ as $$Base } from './Base_Bzt3yfpW.mjs';
import { $ as $$PlenoCard } from './PlenoCard_RiQqZPId.mjs';
import { c as getPlenosFiltrados } from './supabase_Cxhp8T3W.mjs';

const prerender = false;
const $$Actas = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Actas;
  const page = Number(Astro2.url.searchParams.get("page") ?? 1);
  const municipio = Astro2.url.searchParams.get("municipio") ?? void 0;
  const { data: plenos, count } = await getPlenosFiltrados({ page, municipio });
  const totalPages = Math.ceil(count / 20);
  return renderTemplate`${renderComponent($$result, "Base", $$Base, { "title": "Actas de plenos", "description": "Archivo completo de actas de plenos municipales de San Sebastián. Consulta todas las sesiones y decisiones del Ayuntamiento." }, { "default": async ($$result2) => renderTemplate` ${maybeRenderHead()}<div class="max-w-3xl"> <div class="section-rule mb-6"> <h1 class="text-xs font-bold uppercase tracking-widest">Actas de plenos</h1> </div> ${plenos.length === 0 ? renderTemplate`<p class="text-[var(--color-ink-muted)]">No hay actas procesadas aún.</p>` : renderTemplate`${renderComponent($$result2, "Fragment", Fragment, {}, { "default": async ($$result3) => renderTemplate` <div class="space-y-0"> ${plenos.map((p) => renderTemplate`${renderComponent($$result3, "PlenoCard", $$PlenoCard, { "pleno": p })}`)} </div>  ${totalPages > 1 && renderTemplate`<nav class="flex justify-between items-center mt-8 pt-4 border-t border-[var(--color-border)]"> ${page > 1 ? renderTemplate`<a${addAttribute(`/actas?page=${page - 1}`, "href")} class="text-sm font-semibold hover:underline">← Más recientes</a>` : renderTemplate`<span></span>`} <span class="text-xs text-[var(--color-ink-muted)]">
Página ${page} de ${totalPages} </span> ${page < totalPages ? renderTemplate`<a${addAttribute(`/actas?page=${page + 1}`, "href")} class="text-sm font-semibold hover:underline">Anteriores →</a>` : renderTemplate`<span></span>`} </nav>`}` })}`} </div> ` })}`;
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/actas.astro", void 0);

const $$file = "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/actas.astro";
const $$url = "/actas";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Actas,
  file: $$file,
  prerender,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
