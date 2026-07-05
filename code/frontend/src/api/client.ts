/**
 * API 客户端模块
 *
 * 封装与后端 FastAPI 服务的 HTTP 通信。
 * 通过 window.__READBOX_CONFIG__ 动态获取后端地址（端口由 Tauri 分配）。
 */
import axios from "axios";

/**
 * 获取后端基础 URL
 *
 * 端口由 Tauri Rust 层在启动时随机分配，
 * 通过 window.__READBOX_CONFIG__ 传递给前端。
 * 开发模式下（未通过 Tauri 启动）使用默认端口。
 */
export function getBaseUrl(): string {
  const config = window.__READBOX_CONFIG__;
  // Tauri 模式下从 __READBOX_CONFIG__ 读取端口
  // 浏览器开发模式默认使用后端端口 8765
  const port = config?.port ?? 8765;
  return `http://127.0.0.1:${port}`;
}

// 创建 Axios 实例
// 注意：不设默认 Content-Type，让 Axios 根据请求数据自动选择
// 发送 JSON 时自动用 application/json
// 发送 FormData 时自动用 multipart/form-data
const apiClient = axios.create({
  baseURL: getBaseUrl(),  // 初始默认值，拦截器会每次更新
  timeout: 5000,          // 请求超时时间：5 秒
});

// 请求拦截器：每次请求前动态设置 baseURL
apiClient.interceptors.request.use((config) => {
  config.baseURL = getBaseUrl();
  return config;
});

// --- 类型定义 ---

/** 健康检查响应 */
export interface HealthResponse {
  status: string;     // "ok" 表示服务正常
  version: string;    // 后端版本号
  timestamp: string;  // 响应时间戳
}

/** 应用配置响应 */
export interface ConfigResponse {
  db_version: number;    // 数据库版本
  app_version: string;   // 应用版本
}

// --- API 方法 ---

/** 调用后端健康检查接口 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>("/api/health");
  return response.data;
}

/** 获取应用配置信息 */
export async function getConfig(): Promise<ConfigResponse> {
  const response = await apiClient.get<ConfigResponse>("/api/config");
  return response.data;
}

export default apiClient;
