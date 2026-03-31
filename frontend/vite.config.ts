import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteStaticCopy } from 'vite-plugin-static-copy'

export default defineConfig({
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        {
          src: 'node_modules/@ricky0123/vad-web/dist/vad.worklet.bundle.min.js',
          dest: 'vad',
        },
        {
          src: 'node_modules/@ricky0123/vad-web/dist/silero_vad_v5.onnx',
          dest: 'vad',
        },
        {
          src: 'node_modules/@ricky0123/vad-web/dist/silero_vad_legacy.onnx',
          dest: 'vad',
        },
        {
          src: 'node_modules/onnxruntime-web/dist/*.wasm',
          dest: 'vad',
        },
        {
          src: 'node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded*.mjs',
          dest: 'vad',
        },
      ],
    }),
  ],
  server: {
    host: '127.0.0.1',
    port: 5180,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  preview: {
    host: '127.0.0.1',
    port: 4180,
    strictPort: true,
  },
})
