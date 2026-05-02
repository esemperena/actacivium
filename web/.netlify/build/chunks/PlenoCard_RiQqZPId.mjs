import { c as createComponent } from './astro-component_7ATDtAtY.mjs';
import 'piccolore';
import { m as maybeRenderHead, f as addAttribute, r as renderTemplate } from './ssr-function_DV3Szxnz.mjs';
import 'clsx';

const $$PlenoCard = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$PlenoCard;
  const { pleno, featured = false } = Astro2.props;
  const fecha = /* @__PURE__ */ new Date(pleno.fecha + "T12:00:00");
  const fechaLarga = fecha.toLocaleDateString("es-ES", {
    day: "numeric",
    month: "long",
    year: "numeric"
  });
  const diaSemana = fecha.toLocaleDateString("es-ES", { weekday: "long" });
  const esExtraordinaria = pleno.tipo_sesion === "extraordinaria";
  return renderTemplate`${maybeRenderHead()}<article${addAttribute([
    "border-b border-[var(--color-border)] group",
    featured ? "pb-8 mb-2" : "py-5"
  ], "class:list")}> <!-- Etiquetas superiores --> <div class="flex flex-wrap items-center gap-2 mb-2"> <span class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-ink-muted)]">
Pleno nº ${pleno.numero_acta} </span> ${esExtraordinaria && renderTemplate`<span class="badge bg-amber-100 text-amber-800">Extraordinaria</span>`} </div> <!-- Título / fecha --> <a${addAttribute(`/acta/${pleno.id}`, "href")} class="block"> <time${addAttribute(pleno.fecha, "datetime")}${addAttribute([
    "font-serif font-bold block mb-1 group-hover:text-[var(--color-accent)] transition-colors",
    featured ? "headline-lg" : "headline-md"
  ], "class:list")} style="text-transform: capitalize;"> ${diaSemana}, ${fechaLarga} </time> ${pleno.resumen_ia && renderTemplate`<p${addAttribute([
    "text-[var(--color-ink-muted)] leading-relaxed mt-1",
    featured ? "text-base" : "text-sm"
  ], "class:list")}> ${pleno.resumen_ia.length > 200 ? pleno.resumen_ia.slice(0, 200) + "…" : pleno.resumen_ia} </p>`} </a> <!-- Stats del pleno --> <div class="flex flex-wrap items-center gap-x-5 gap-y-1 mt-3 text-xs text-[var(--color-ink-muted)] font-sans"> <span class="font-medium text-[var(--color-ink)]"> ${pleno.total_puntos} ${pleno.total_puntos === 1 ? "punto" : "puntos"} </span> ${pleno.aprobados > 0 && renderTemplate`<span class="resultado-aprobado">${pleno.aprobados} aprobados</span>`} ${pleno.rechazados > 0 && renderTemplate`<span class="resultado-rechazado">${pleno.rechazados} rechazados</span>`} ${pleno.unanimes > 0 && renderTemplate`<span>${pleno.unanimes} por unanimidad</span>`} ${pleno.n_asistentes && renderTemplate`<span>${pleno.n_asistentes} concejales</span>`} <a${addAttribute(`/acta/${pleno.id}`, "href")} class="ml-auto text-[var(--color-accent)] font-semibold hover:underline">
Ver acta →
</a> </div> </article>`;
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/components/PlenoCard.astro", void 0);

export { $$PlenoCard as $ };
