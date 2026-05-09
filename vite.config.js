import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const standalone = mode === "standalone";

  return {
    base: standalone ? "/" : "/static/spa/",
    envDir: ".",
    plugins: [react()],
    root: "frontend",
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: env.VITE_API_BASE_URL
        ? undefined
        : {
            "/api": {
              target: env.VITE_DEV_PROXY_TARGET || "http://127.0.0.1:8000",
              changeOrigin: true,
            },
            "/health": {
              target: env.VITE_DEV_PROXY_TARGET || "http://127.0.0.1:8000",
              changeOrigin: true,
            },
          },
    },
    build: {
      outDir: standalone ? "../frontend/dist" : "../app/static/spa",
      emptyOutDir: true,
      sourcemap: false,
      rollupOptions: {
        output: {
          entryFileNames: "index.js",
          chunkFileNames: "chunks/[name].js",
          assetFileNames: (assetInfo) => (assetInfo.name === "style.css" ? "index.css" : "assets/[name][extname]"),
          manualChunks: {
            react: ["react", "react-dom", "react-router-dom"],
            motion: ["framer-motion"],
            charts: ["recharts"],
            dnd: ["@dnd-kit/core", "@dnd-kit/utilities"],
            icons: ["lucide-react"],
            toast: ["react-hot-toast"],
          },
        },
      },
    },
  };
});
