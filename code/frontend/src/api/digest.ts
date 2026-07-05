/**
 * 提炼 API 客户端
 *
 * 提供调用 AI 提炼相关的接口方法。
 */
import apiClient from "./client";

/** 提炼进度 */
export interface DigestStatus {
  digest_id: number | null;
  status: string;
  total: number;
  processed: number;
}

/** 章节提炼结果 */
export interface ChapterDigestResult {
  summary: string;
  concepts: { term: string; explanation: string }[];
  quotes: { quote: string; reason: string }[];
}

/** 启动全书提炼（超时 120 秒，因 LLM 逐章处理较慢） */
export async function startDigest(bookId: number): Promise<{ digest_id: number; status: string }> {
  const response = await apiClient.post(`/api/digest/${bookId}/start`, undefined, {
    timeout: 120000,
  });
  return response.data;
}

/** 查询提炼进度 */
export async function getDigestStatus(bookId: number): Promise<DigestStatus> {
  const response = await apiClient.get(`/api/digest/${bookId}/status`);
  return response.data;
}

/** 获取单章提炼结果 */
export async function getChapterDigest(
  bookId: number,
  chapterId: number
): Promise<ChapterDigestResult> {
  const response = await apiClient.get(`/api/digest/${bookId}/chapters/${chapterId}`);
  return response.data;
}

/** 单章提炼 */
export async function digestChapter(
  bookId: number,
  chapterId: number
): Promise<{ status: string }> {
  const response = await apiClient.post(`/api/digest/${bookId}/chapters/${chapterId}`);
  return response.data;
}

/** 导出 Markdown 笔记 */
export async function exportDigest(bookId: number): Promise<Blob> {
  const response = await apiClient.get(`/api/digest/${bookId}/export`, {
    responseType: "blob",
  });
  return response.data;
}
