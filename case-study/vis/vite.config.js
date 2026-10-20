import { defineConfig } from 'vite';

// Relative base so the app works from any sub-path (e.g. /vis/ on GitHub Pages).
// Muvin hardcodes "../assets/*.svg" (relative to the page); point it to ./assets/ (see public/assets).
const muvinAssets = {
  name: 'muvin-assets',
  transform(code, id) {
    if (id.includes('muvin') && code.includes('../assets/')) {
      return code.replaceAll('../assets/', './assets/');
    }
  },
};

export default defineConfig({
  base: './',
  plugins: [muvinAssets],
  optimizeDeps: { exclude: ['muvin'] },
});
