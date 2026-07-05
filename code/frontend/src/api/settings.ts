/**
 * 设置 API 客户端
 *
 * 提供 LLM Provider 配置的读写接口。
 */
import apiClient from "./client";

/** LLM 配置项 */
export interface LlmSettings {
  llm_provider: string;
  llm_api_key: string;
  llm_api_base: string;
  llm_model: string;
  llm_max_tokens: string;
  llm_temperature: string;
}

/** 获取 LLM 配置 */
export async function getLlmSettings(): Promise<LlmSettings> {
  const response = await apiClient.get("/api/settings/llm");
  return response.data;
}

/** 保存 LLM 配置 */
export async function saveLlmSettings(
  settings: Partial<LlmSettings>
): Promise<void> {
  await apiClient.post("/api/settings/llm", settings);
}
