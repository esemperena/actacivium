import { c as createComponent } from './astro-component_7ATDtAtY.mjs';
import 'piccolore';
import { k as createRenderInstruction, i as renderComponent, r as renderTemplate, m as maybeRenderHead } from './ssr-function_DV3Szxnz.mjs';
import { $ as $$Base } from './Base_Bzt3yfpW.mjs';

async function renderScript(result, id) {
  const inlined = result.inlinedScripts.get(id);
  let content = "";
  if (inlined != null) {
    if (inlined) {
      content = `<script type="module">${inlined}</script>`;
    }
  } else {
    const resolved = await result.resolve(id);
    content = `<script type="module" src="${result.userAssetsBase ? (result.base === "/" ? "" : result.base) + result.userAssetsBase : ""}${resolved}"></script>`;
  }
  return createRenderInstruction({ type: "script", id, content });
}

const $$Newsletter = createComponent(async ($$result, $$props, $$slots) => {
  return renderTemplate`${renderComponent($$result, "Base", $$Base, { "title": "Newsletter · Acta Civium", "description": "Suscríbete a Acta Civium y recibe cada semana un resumen de los acuerdos municipales que más afectan a la ciudadanía." }, { "default": async ($$result2) => renderTemplate` ${maybeRenderHead()}<div class="max-w-2xl mx-auto"> <div class="section-rule mb-8"> <span class="text-xs font-bold uppercase tracking-widest">Newsletter</span> </div> <h1 class="headline-xl mb-4">El pleno en tu bandeja de entrada</h1> <p class="text-lg text-[var(--color-ink-muted)] leading-relaxed mb-8">
Cada semana, cuando hay un nuevo pleno, te enviamos un resumen de las decisiones
      que más importan: vivienda, urbanismo, servicios sociales, medio ambiente.
      Sin burocracia, en lenguaje ciudadano.
</p> <!-- Formulario Brevo --> <div class="bg-white border border-[var(--color-border)] p-8 mb-10"> <form id="newsletter-form" class="space-y-4"> <div> <label for="email" class="block text-sm font-semibold mb-1">Tu correo electrónico</label> <input type="email" id="email" name="email" required placeholder="nombre@ejemplo.com" class="w-full border border-[var(--color-border)] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"> </div> <button type="submit" class="w-full bg-[var(--color-accent)] text-white font-bold py-3 text-sm hover:bg-[#0f2a1a] transition-colors">
Suscribirme →
</button> <p class="text-xs text-[var(--color-ink-muted)] text-center">
Sin spam. Frecuencia: cuando hay pleno nuevo (cada 3-6 semanas).
          Puedes darte de baja en cualquier momento.
</p> </form> <div id="form-success" class="hidden text-center py-4"> <p class="font-serif text-lg font-bold text-[var(--color-accent)] mb-1">¡Suscripción confirmada!</p> <p class="text-sm text-[var(--color-ink-muted)]">Te avisaremos cuando haya nuevo pleno.</p> </div> </div> <!-- Qué incluye --> <div class="section-rule mb-6"> <span class="text-xs font-bold uppercase tracking-widest">Qué incluye cada número</span> </div> <ul class="space-y-4 mb-10"> ${[
    ["Resumen ejecutivo", "Las 3-5 decisiones más importantes del pleno en lenguaje ciudadano."],
    ["Votaciones clave", "Quién votó qué y por qué importa. Qué rechazó la mayoría."],
    ["Enfoque social y ambiental", "Impacto en vivienda, servicios sociales, medio ambiente y derechos."],
    ["Fuente siempre accesible", "Enlace al acta oficial y a nuestra base de datos para profundizar."]
  ].map(([titulo, desc]) => renderTemplate`<li class="flex gap-4 border-b border-[var(--color-border)] pb-4 last:border-0"> <span class="text-[var(--color-accent)] font-serif font-bold text-xl leading-none mt-0.5">·</span> <div> <p class="font-semibold text-sm">${titulo}</p> <p class="text-sm text-[var(--color-ink-muted)]">${desc}</p> </div> </li>`)} </ul> </div> ` })} ${renderScript($$result, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/newsletter.astro?astro&type=script&index=0&lang.ts")}`;
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/newsletter.astro", void 0);

const $$file = "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/pages/newsletter.astro";
const $$url = "/newsletter";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Newsletter,
  file: $$file,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
