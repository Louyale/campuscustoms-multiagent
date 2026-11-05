import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The board runs on http://localhost:5173 and talks to the FastAPI backend at http://localhost:8000
// (set VITE_API_URL to change it). The backend allows this origin in its CORS settings.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
});
