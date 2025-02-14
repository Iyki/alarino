import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  server: {
    proxy: {
      // todo: change to environment variable: REACT_APP_API_URL, docker??
      '/api': 'http://localhost:5001' 
    }
  },
})
