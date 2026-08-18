import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      // We hand-author public/manifest.json (name, theme_color from the
      // saffron_orange token, signboard-motif icon) and link it directly
      // in index.html -- this plugin only adds the service worker for
      // offline app-shell caching. Full offline logging is Phase 5.
      manifest: false,
      registerType: "autoUpdate",
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg}"],
      },
    }),
  ],
});
