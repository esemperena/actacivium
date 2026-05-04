// @ts-check
import { defineConfig } from 'astro/config';
import netlify from '@astrojs/netlify';
import tailwindcss from '@tailwindcss/vite';
import react from '@astrojs/react';

const isBuild = process.argv.includes('build');

export default defineConfig({
  site: 'https://actacivium.netlify.app',
  output: 'server',
  adapter: isBuild ? netlify() : undefined,
  integrations: [react()],
  vite: {
    plugins: [tailwindcss()],
  },
});
