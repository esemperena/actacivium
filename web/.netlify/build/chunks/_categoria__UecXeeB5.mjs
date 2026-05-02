import { c as createComponent } from './astro-component_7ATDtAtY.mjs';
import 'piccolore';
import { m as maybeRenderHead, f as addAttribute, r as renderTemplate, i as renderComponent } from './ssr-function_DV3Szxnz.mjs';
import { $ as $$Base } from './Base_Bzt3yfpW.mjs';
import 'clsx';
import { C as CATEGORIAS, s as supabase } from './supabase_Cxhp8T3W.mjs';

const $$PuntoItem = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$PuntoItem;
  const { punto } = Astro2.props;
  const CATEGORIAS = {
    urbanismo: "Urbanismo",
    vivienda: "Vivienda",
    hacienda: "Hacienda",
    medio_ambiente: "Medio Ambiente",
    servicios_sociales: "Serv. Sociales",
    movilidad: "Movilidad",
    cultura: "Cultura",
    gobernanza: "Gobernanza",
    derechos: "Derechos",
    seguridad: "Seguridad",
    educacion: "Educación",
    otro: "Otro"
  };
  const RESULTADO_LABEL = {
    aprobado: "Aprobado",
    rechazado: "Rechazado",
    enterado: "Enterado",
    retirado: "Retirado",
    sin_votacion: "—"
  };
  const categoriaLabel = CATEGORIAS[punto.categoria] ?? punto.categoria;
  const resultadoLabel = RESULTADO_LABEL[punto.resultado] ?? punto.resultado;
  const esRelevante = (punto.relevancia_social ?? 0) >= 4;
  return renderTemplate`${maybeRenderHead()}<li${addAttribute([
    "py-4 border-b border-[var(--color-border)] last:border-0",
    esRelevante && "border-l-2 border-l-[var(--color-accent)] pl-3 ml-[-0.75rem]"
  ], "class:list")}> <div class="flex flex-wrap items-start gap-x-3 gap-y-1 mb-1"> <span class="text-xs text-[var(--color-ink-muted)] font-mono">${punto.numero}.</span> <span${addAttribute(["badge", `badge-${punto.categoria}`], "class:list")}> ${categoriaLabel} </span> ${punto.es_urgencia && renderTemplate`<span class="badge" style="background:#fef2f2;color:#991b1b;">Urgencia</span>`} <span${addAttribute([
    "text-xs font-semibold ml-auto",
    punto.resultado === "aprobado" && "resultado-aprobado",
    punto.resultado === "rechazado" && "resultado-rechazado",
    punto.resultado === "enterado" && "resultado-enterado"
  ], "class:list")}> ${resultadoLabel} ${punto.unanimidad && punto.resultado === "aprobado" && renderTemplate`<span class="font-normal text-[var(--color-ink-muted)]"> · unanimidad</span>`} </span> </div> <p class="text-sm font-serif font-medium leading-snug">${punto.titulo}</p> ${punto.resumen_ia && renderTemplate`<p class="text-xs text-[var(--color-ink-muted)] mt-1 leading-relaxed"> ${punto.resumen_ia} </p>`} ${esRelevante && renderTemplate`<div class="mt-1 flex items-center gap-1"> ${Array.from({ length: punto.relevancia_social ?? 0 }).map(() => renderTemplate`<span class="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)]"></span>`)} <span class="text-[10px] text-[var(--color-ink-muted)] ml-1">Alta relevancia ciudadana</span> </div>`} </li>`;
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/components/PuntoItem.astro", void 0);

const prerender = false;
const $$categoria = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$categoria;
  const { categoria } = Astro2.params;
  if (!categoria || !CATEGORIAS[categoria]) {
    return Astro2.redirect("/temas");
  }
  const label = CATEGORIAS[categoria];
  const { data: puntos } = await supabase.from("puntos").select(`
    id, numero, titulo, categoria, tipo, resultado,
    unanimidad, resumen_ia, relevancia_social, es_urgencia, pleno_id,
    plenos ( fecha, numero_acta )
  `).eq("categoria", categoria).order("relevancia_social", { ascending: false }).limit(50);
  return renderTemplate`${renderComponent($$result, "Base", $$Base, { "title": `${label} · Plenos de San Sebastián`, "description": `Todas las decisiones sobre ${label.toLowerCase()} en los plenos municipales de San Sebastián.` }, { "default": async ($$result2) => renderTemplate` ${maybeRenderHead()}<div class="max-w-3xl"> <div class="section-rule mb-6"> <div class="flex items-center gap-3"> <span${addAttribute(["badge", `badge-${categoria}`], "class:list")}>${label}</span> <h1 class="text-xs font-bold uppercase tracking-widest"> ${puntos?.length ?? 0} decisiones encontradas
</h1> </div> </div> <p class="text-sm text-[var(--color-ink-muted)] mb-8">
Todos los puntos del orden del día relacionados con <strong>${label.toLowerCase()}</strong> en los plenos municipales de San Sebastián, ordenados por relevancia ciudadana.
</p> ${!puntos || puntos.length === 0 ? renderTemplate`<p class="text-[var(--color-ink-muted)]">Aún no hay datos para esta categoría.</p>` : renderTemplate`<ul> ${puntos.map((p) => renderTemplate`<li> <div class="text-xs text-[var(--color-ink-muted)] pt-4 pb-1"> <a${addAttribute(`/acta/${p.pleno_id}`, "href")} class="hover:underline">
Pleno nº ${p.plenos?.numero_acta} ·${" "} ${new Date(p.plenos?.fecha).toLocaleDateString("es-ES", {
    day: "numeric",
    month: "long",
    year: "numeric"
  })} </a> </div> ${renderComponent($$result2, "PuntoItem", $$PuntoItem, { "punto": p })} </li>`)} </ul>`} </div> ` })}`;
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/temas/[categoria].astro", void 0);

const $$file = "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/temas/[categoria].astro";
const $$url = "/temas/[categoria]";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$categoria,
  file: $$file,
  prerender,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
