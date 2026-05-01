// @ts-check
import { defineConfig } from 'astro/config';
import netlify from '@astrojs/netlify';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  output: 'hybrid',   // estático por defecto; SSR donde se marque
  adapter: netlify(),
  vite: {
    plugins: [tailwindcss()],
  },
});