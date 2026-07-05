/**
 * 问答 API 客户端
 *
 * 提供基于书籍内容的问答接口。
 * 支持流式回答（SSE）、清空上下文、获取历史。
 */

import apiClient, { getBaseUrl } from "./client";

/** 对话消息 */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/** 提问：返回 EventSource 流 */
export function askQuestionStream(
  bookId: number,
  question: string,
  onData: (chunk: string) => void,
  onDone: () => void,
  onError: (err: Error) => void
): AbortController {
  const controller = new AbortController();

  fetch(`${getBaseUrl()}/api/qa/${bookId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.body) {
        onError(new Error("无响应体"));
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const raw = line.slice(6);
            try {
              const parsed = JSON.parse(raw);
              if (parsed.t === "[DONE]") {
                onDone();
                return;
              }
              onData(parsed.t || "");
            } catch {
              // 兼容非 JSON 格式（旧版）
              if (raw === "[DONE]") { onDone(); return; }
              onData(raw);
            }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onError(err);
      }
    });

  return controller;
}

/** 清空对话上下文 */
export async function clearContext(bookId: number): Promise<void> {
  await apiClient.post(`/api/qa/${bookId}/clear`);
}

/** 获取对话历史 */
export async function getHistory(
  bookId: number
): Promise<{ history: ChatMessage[] }> {
  const response = await apiClient.get(`/api/qa/${bookId}/history`);
  return response.data;
}
