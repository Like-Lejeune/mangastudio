import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Les routes sont les fichiers de src/routes ; src/routeTree.gen.ts est généré automatiquement.
export default defineConfig({
  plugins: [tanstackRouter({ target: "react", autoCodeSplitting: true }), react(), tailwindcss()],
  resolve: { alias: { "@": "/src" } },
  // En local, les liens de partage (/lire/…) sont servis par l'API, comme Caddy le fait en production.
  server: { proxy: { "/lire": "http://localhost:8000" } },
});
