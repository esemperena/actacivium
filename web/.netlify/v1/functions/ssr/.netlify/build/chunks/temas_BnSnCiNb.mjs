import { c as createComponent } from './astro-component_7ATDtAtY.mjs';
import 'piccolore';
import { i as renderComponent, r as renderTemplate, m as maybeRenderHead, f as addAttribute } from './ssr-function_DV3Szxnz.mjs';
import { $ as $$Base } from './Base_Bzt3yfpW.mjs';
import { C as CATEGORIAS } from './supabase_Cxhp8T3W.mjs';

const $$Temas = createComponent(($$result, $$props, $$slots) => {
  return renderTemplate`${renderComponent($$result, "Base", $$Base, { "title": "Temas · Acta Civium", "description": "Explora las decisiones del Ayuntamiento de San Sebastián por tema: vivienda, urbanismo, medio ambiente, servicios sociales y más." }, { "default": ($$result2) => renderTemplate` ${maybeRenderHead()}<div class="max-w-3xl"> <div class="section-rule mb-6"> <h1 class="text-xs font-bold uppercase tracking-widest">Explorar por tema</h1> </div> <div class="grid sm:grid-cols-2 gap-3"> ${Object.entries(CATEGORIAS).filter(([k]) => k !== "otro").map(([slug, label]) => renderTemplate`<a${addAttribute(`/temas/${slug}`, "href")} class="flex items-center gap-3 border border-[var(--color-border)] p-4 hover:border-[var(--color-ink)] transition-colors"> <span${addAttribute(["badge", `badge-${slug}`], "class:list")}>${label}</span> </a>`)} </div> </div> ` })}`;
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/temas.astro", void 0);

const $$file = "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/temas.astro";
const $$url = "/temas";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Temas,
  file: $$file,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
