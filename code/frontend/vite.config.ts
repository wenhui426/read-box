/**
 * Read-Box 前端构建配置
 *
 * 使用 Vite 构建 Vue 3 + TypeScript 项目。
 * strictPort: true 确保开发服务器端口固定（Tauri 依赖此行为）。
 */

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  // Vue 3 单文件组件支持
  plugins: [vue()],
  server: {
    // 固定端口：Tauri 配置中的 devUrl 依赖此端口不变
    strictPort: true,
  },
  // 关闭 Vite 的启动信息清屏，保留终端上下文
  clearScreen: false,
});
