import { c as createComponent } from './astro-component_7ATDtAtY.mjs';
import 'piccolore';
import { i as renderComponent, r as renderTemplate, m as maybeRenderHead, f as addAttribute } from './ssr-function_DV3Szxnz.mjs';
import { $ as $$Base } from './Base_Bzt3yfpW.mjs';
import { f as getMunicipios, s as supabase } from './supabase_Cxhp8T3W.mjs';

const prerender = false;
const $$Index = createComponent(async ($$result, $$props, $$slots) => {
  const municipios = await getMunicipios();
  let totalActas = 0, totalPuntos = 0;
  try {
    const [a, p] = await Promise.all([
      supabase.from("plenos").select("*", { count: "exact", head: true }).eq("estado", "procesado"),
      supabase.from("puntos").select("*", { count: "exact", head: true })
    ]);
    totalActas = a.count ?? 0;
    totalPuntos = p.count ?? 0;
  } catch {
  }
  return renderTemplate`${renderComponent($$result, "Base", $$Base, { "title": "Acta Civium", "description": "Los plenos municipales en lenguaje ciudadano. Analizamos las actas del Ayuntamiento y te enviamos lo que importa cada semana." }, { "default": async ($$result2) => renderTemplate`  ${maybeRenderHead()}<section class="-mx-4 md:-mx-8 -mt-8 bg-[var(--color-accent)] text-white py-24 px-4 md:px-8"> <div class="max-w-2xl mx-auto text-center"> <p class="text-xs font-bold uppercase tracking-[0.2em] text-green-300 mb-5">
Transparencia Municipal · España
</p> <h1 class="font-serif text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-6" style="letter-spacing:-0.02em;">
Lo que decide el Ayuntamiento,<br> <em class="not-italic text-green-300">en lenguaje que se entiende.</em> </h1> <p class="text-green-200 text-lg leading-relaxed mb-10 max-w-lg mx-auto">
Analizamos las actas de los plenos municipales y las convertimos
        en información útil para la ciudadanía. Newsletter semanal, gratuito.
</p> <form action="/newsletter" method="GET" class="flex flex-col sm:flex-row gap-3 max-w-md mx-auto mb-6"> <input type="email" name="email" placeholder="tu@email.com" required class="flex-1 px-4 py-3 text-[var(--color-ink)] text-sm focus:outline-none focus:ring-2 focus:ring-white"> <button type="submit" class="bg-white text-[var(--color-accent)] font-bold text-sm px-7 py-3 hover:bg-green-50 transition-colors cursor-pointer whitespace-nowrap">
Suscribirme gratis →
</button> </form> <p class="text-green-500 text-xs">Sin spam · Un correo semanal · Cancelar cuando quieras</p> ${totalActas > 0 && renderTemplate`<div class="flex justify-center gap-8 mt-10 pt-8 border-t border-green-800 text-sm text-green-300"> <span><strong class="text-white text-xl font-serif">${totalActas}</strong> actas analizadas</span> <span><strong class="text-white text-xl font-serif">${totalPuntos}</strong> puntos del orden del día</span> <span><strong class="text-white text-xl font-serif">${municipios.length}</strong> ${municipios.length === 1 ? "municipio" : "municipios"}</span> </div>`} </div> </section>  <section class="py-16 border-b border-[var(--color-border)]"> <div class="max-w-4xl mx-auto"> <div class="section-rule mb-8"> <span class="text-xs font-bold uppercase tracking-widest">Municipios cubiertos</span> </div> ${municipios.length === 0 ? renderTemplate`<p class="text-[var(--color-ink-muted)] text-sm">Cargando municipios…</p>` : renderTemplate`<div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"> ${municipios.map((m) => renderTemplate`<a${addAttribute(`/ciudad/${m.slug}`, "href")} class="group border border-[var(--color-border)] bg-white p-5 hover:border-[var(--color-ink)] hover:shadow-sm transition-all"> <!-- Color stripe from governing party --> <div class="h-1 w-8 mb-4 rounded-sm"${addAttribute(`background: ${m.color_gobierno ?? "#1a3a2a"}`, "style")}></div> <p class="font-serif font-bold text-lg leading-tight group-hover:text-[var(--color-accent)] transition-colors"> ${m.nombre} ${m.nombre_alt && m.nombre_alt !== m.nombre && renderTemplate`<span class="text-sm font-normal text-[var(--color-ink-muted)] ml-1">· ${m.nombre_alt}</span>`} </p> <p class="text-xs text-[var(--color-ink-muted)] mt-1">${m.provincia} · ${m.comunidad}</p> <div class="mt-4 pt-3 border-t border-[var(--color-border)] flex items-center justify-between text-xs"> <span class="text-[var(--color-ink-muted)]"> ${m.partido_gobierno ? renderTemplate`<span>Gobierno: <strong>${m.partido_gobierno}</strong></span>` : "Plenos analizados"} </span> <span class="font-semibold text-[var(--color-accent)] group-hover:underline">
Ver plenos →
</span> </div> </a>`)} <!-- Próximamente card --> <div class="border border-dashed border-[var(--color-border)] p-5 flex flex-col justify-center items-center text-center opacity-60"> <p class="text-2xl mb-2">+</p> <p class="font-semibold text-sm">Más municipios</p> <p class="text-xs text-[var(--color-ink-muted)] mt-1">Próximamente</p> </div> </div>`} </div> </section>  <section class="py-16 border-b border-[var(--color-border)]"> <div class="max-w-3xl mx-auto"> <div class="section-rule mb-10"> <span class="text-xs font-bold uppercase tracking-widest">Cómo funciona</span> </div> <div class="grid md:grid-cols-3 gap-8"> ${[
    {
      num: "01",
      title: "Descargamos el acta",
      desc: "Monitorizamos el portal de cada Ayuntamiento y descargamos automáticamente cada acta publicada."
    },
    {
      num: "02",
      title: "Analizamos el contenido",
      desc: "Extraemos los puntos del orden del día, los clasificamos por tema y detectamos quién votó qué."
    },
    {
      num: "03",
      title: "Te lo enviamos",
      desc: "Recibes un resumen semanal con las decisiones que afectan a tu ciudad, claro y sin tecnicismos."
    }
  ].map(({ num, title, desc }) => renderTemplate`<div> <p class="font-serif text-4xl font-bold text-[var(--color-accent)] mb-3">${num}</p> <h3 class="font-semibold text-base mb-2">${title}</h3> <p class="text-sm text-[var(--color-ink-muted)] leading-relaxed">${desc}</p> </div>`)} </div> </div> </section>  <section class="-mx-4 md:-mx-8 bg-[var(--color-accent-light)] py-16 px-4 md:px-8"> <div class="max-w-md mx-auto text-center"> <h2 class="font-serif text-2xl font-bold mb-3">No te pierdas ningún pleno</h2> <p class="text-[var(--color-ink-muted)] text-sm mb-6 leading-relaxed">
Suscríbete a la newsletter y recibe cada semana el análisis de los
        acuerdos municipales de tu ciudad.
</p> <form action="/newsletter" method="GET" class="flex flex-col sm:flex-row gap-3 max-w-sm mx-auto"> <input type="email" name="email" placeholder="tu@email.com" required class="flex-1 px-4 py-3 text-sm border border-[var(--color-border)] focus:outline-none focus:border-[var(--color-ink)]"> <button type="submit" class="bg-[var(--color-accent)] text-white font-bold text-sm px-6 py-3 hover:bg-[#0f2218] transition-colors cursor-pointer">
Suscribirme
</button> </form> </div> </section> ` })}`;
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/index.astro", void 0);

const $$file = "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/index.astro";
const $$url = "";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Index,
  file: $$file,
  prerender,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
