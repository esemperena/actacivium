import { c as createComponent } from './astro-component_7ATDtAtY.mjs';
import 'piccolore';
import { r as renderTemplate, l as renderSlot, n as renderHead, u as unescapeHTML, f as addAttribute } from './ssr-function_DV3Szxnz.mjs';
import 'clsx';

var __freeze = Object.freeze;
var __defProp = Object.defineProperty;
var __template = (cooked, raw) => __freeze(__defProp(cooked, "raw", { value: __freeze(cooked.slice()) }));
var _a;
const $$Base = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Base;
  const {
    title,
    description = "Acta Civium analiza los plenos municipales de San Sebastián con una mirada ciudadana, social y medioambiental.",
    ogImage = "/og-default.png"
  } = Astro2.props;
  const canonicalURL = new URL(Astro2.url.pathname, Astro2.site ?? "https://actacivium.netlify.app");
  const fullTitle = title === "Acta Civium" ? title : `${title} — Acta Civium`;
  return renderTemplate(_a || (_a = __template(['<html lang="es"> <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="canonical"', '><meta name="description"', '><!-- Open Graph --><meta property="og:title"', '><meta property="og:description"', '><meta property="og:image"', '><meta property="og:url"', '><meta property="og:type" content="website"><meta property="og:locale" content="es_ES"><!-- Twitter --><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title"', '><meta name="twitter:description"', '><meta name="twitter:image"', '><!-- Schema.org --><script type="application/ld+json">', "<\/script><title>", '</title><link rel="icon" type="image/svg+xml" href="/favicon.svg"><link rel="sitemap" href="/sitemap-index.xml">', '</head> <body class="min-h-screen flex flex-col"> <!-- Franja de cabecera superior --> <div class="border-b border-[var(--color-border)] py-1 px-4 text-xs text-[var(--color-ink-muted)] flex justify-between items-center"> <span>San Sebastián · Plenos Municipales</span> <a href="/newsletter" class="font-semibold text-[var(--color-accent)] hover:underline">\nSuscríbete a la newsletter →\n</a> </div> <!-- Cabecera principal --> <header class="border-b-4 border-[var(--color-ink)] py-4 px-4 md:px-8"> <div class="max-w-7xl mx-auto"> <div class="text-center border-b border-[var(--color-border)] pb-4 mb-4"> <a href="/" class="inline-block"> <span class="headline-xl tracking-tight" style="letter-spacing: -0.02em;">Acta Civium</span> </a> <p class="text-[var(--color-ink-muted)] text-sm mt-1 font-sans">\nLos plenos municipales, en lenguaje ciudadano\n</p> </div> <!-- Navegación --> <nav class="flex flex-wrap gap-x-6 gap-y-2 justify-center text-sm font-semibold uppercase tracking-widest text-[var(--color-ink)]"> <a href="/" class="hover:text-[var(--color-accent)] transition-colors">Inicio</a> <a href="/actas" class="hover:text-[var(--color-accent)] transition-colors">Actas</a> <a href="/temas" class="hover:text-[var(--color-accent)] transition-colors">Por tema</a> <a href="/partidos" class="hover:text-[var(--color-accent)] transition-colors">Partidos</a> <a href="/newsletter" class="hover:text-[var(--color-accent)] transition-colors">Newsletter</a> <a href="/sobre" class="hover:text-[var(--color-accent)] transition-colors">Sobre el proyecto</a> </nav> </div> </header> <main class="flex-1 max-w-7xl mx-auto w-full px-4 md:px-8 py-8"> ', ' </main> <footer class="border-t-2 border-[var(--color-ink)] mt-12 py-8 px-4 md:px-8 bg-[var(--color-ink)] text-[var(--color-bg)]"> <div class="max-w-7xl mx-auto grid md:grid-cols-3 gap-8 text-sm"> <div> <p class="font-serif font-bold text-lg mb-2">Acta Civium</p> <p class="text-gray-400 leading-relaxed">\nTransparencia municipal desde una perspectiva ciudadana, social y medioambiental.\n</p> </div> <div> <p class="font-semibold mb-2 uppercase tracking-wider text-xs text-gray-400">Navegación</p> <ul class="space-y-1 text-gray-300"> <li><a href="/actas" class="hover:text-white transition-colors">Actas de plenos</a></li> <li><a href="/temas" class="hover:text-white transition-colors">Por tema</a></li> <li><a href="/partidos" class="hover:text-white transition-colors">Por partido</a></li> <li><a href="/sobre" class="hover:text-white transition-colors">Sobre el proyecto</a></li> </ul> </div> <div> <p class="font-semibold mb-2 uppercase tracking-wider text-xs text-gray-400">Municipios</p> <ul class="space-y-1 text-gray-300"> <li class="font-medium text-white">San Sebastián · Donostia</li> <li class="text-gray-500 italic">Más municipios próximamente</li> </ul> <p class="mt-4 text-gray-500 text-xs">\nFuente: <a href="https://www.donostia.eus" class="underline hover:text-white">donostia.eus</a> </p> </div> </div> <div class="max-w-7xl mx-auto mt-8 pt-4 border-t border-gray-700 text-xs text-gray-500 flex flex-col md:flex-row justify-between gap-2"> <span>© ', " Acta Civium · Proyecto de código abierto</span> <span>Datos: Ayuntamiento de San Sebastián · Licencia de contenido: CC BY 4.0</span> </div> </footer> </body></html>"])), addAttribute(canonicalURL, "href"), addAttribute(description, "content"), addAttribute(fullTitle, "content"), addAttribute(description, "content"), addAttribute(ogImage, "content"), addAttribute(canonicalURL, "content"), addAttribute(fullTitle, "content"), addAttribute(description, "content"), addAttribute(ogImage, "content"), unescapeHTML(JSON.stringify({
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "Acta Civium",
    "description": description,
    "url": Astro2.site,
    "inLanguage": "es"
  })), fullTitle, renderHead(), renderSlot($$result, $$slots["default"]), (/* @__PURE__ */ new Date()).getFullYear());
}, "C:/Users/EnaitzSemperena/Documents/Claude/Projects/Actas/actacivium/web/src/layouts/Base.astro", void 0);

export { $$Base as $ };
