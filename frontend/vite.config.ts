import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The address the dev server forwards API calls to. API_PROXY_TARGET lets a developer point it at a
// local service on another port. It has no VITE_ prefix, so it never reaches the browser.
const apiTarget = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  base: "/",
  server: {
    // CORS on the live API allows only http://localhost:5173, so Vite must stop and not move to
    // another port when 5173 is taken.
    port: 5173,
    strictPort: true,
    proxy: { "/predict": apiTarget, "/health": apiTarget },
  },
  build: { outDir: "dist" },
  test: { environment: "node", include: ["src/**/*.test.{ts,tsx}"] },
});
