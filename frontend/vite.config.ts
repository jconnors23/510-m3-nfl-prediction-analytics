// Build, dev server, and test settings for the web app.

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The address the dev server forwards API calls to. API_PROXY_TARGET lets a developer point it at a
// local service on another port. It has no VITE_ prefix, so it never reaches the browser.
const apiTarget = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  // Assets load from the site root, which matches the CloudFront origin.
  base: "/",
  server: {
    // CORS on the live API allows only http://localhost:5173, so Vite must stop and not move to
    // another port when 5173 is taken.
    port: 5173,
    strictPort: true,
    // In development the page calls its own address and Vite forwards these paths to the API, so
    // the browser makes no cross-origin request.
    proxy: { "/predict": apiTarget, "/health": apiTarget, "/feedback": apiTarget },
  },
  build: { outDir: "dist" },
  // Most tests run plain functions, so the default environment is node, with no browser stand-in.
  // App.test.tsx and Picker.test.tsx render React components, so each starts with the line
  // "// @vitest-environment jsdom", which switches that one file to jsdom, a browser stand-in.
  test: { environment: "node", include: ["src/**/*.test.{ts,tsx}"] },
});
