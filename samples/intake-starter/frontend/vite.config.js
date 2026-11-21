import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The UI calls /api; in development Vite forwards it to the Spring Boot API.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8080' } },
});
