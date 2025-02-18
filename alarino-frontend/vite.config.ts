import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths"
import { visualizer } from 'rollup-plugin-visualizer'


// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths(), visualizer({ filename: 'bulk-stats.html' }) ],
  server: {
    proxy: {
      // todo: change to environment variable: REACT_APP_API_URL, docker??
      '/api': 'http://localhost:5001' 
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // create a separate chunk for each vendor library
          vendor: ['react', 'react-dom', '@chakra-ui/react', '@emotion/react', '@emotion/styled', 'framer-motion'],
        },
      },
    },
  },
})
