import { defineConfig } from "vite";

export default defineConfig({
  server: { port: 5175, proxy: { "/api": "http://127.0.0.1:8005" } },
  preview: { port: 4175 },
});
