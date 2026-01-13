import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js'

export default defineConfig({
  plugins: [vue(), cssInjectedByJsPlugin()],
  
  // 1. 生产环境路径配置 (必须为相对路径)
  base: './', 
  
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  
  // 2. 开发环境代理配置 (npm run dev 时用到)
  server: {
    proxy: {
      // 【关键修改】添加 /api 代理，否则上传、报警、数据等功能会报 404
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      // 视频流代理
      '/video_feed': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      }
    }
  },
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  }
})