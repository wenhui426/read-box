/**
 * 阅读统计 API 客户端
 */
import apiClient from "./client";

export async function startReading(bookId: number, chapterId: number): Promise<void> {
  await apiClient.post(`/api/reading/start/${bookId}/${chapterId}`);
}

export async function stopReading(bookId: number, chapterId: number): Promise<{ seconds?: number; wpm?: number }> {
  const response = await apiClient.post(`/api/reading/stop/${bookId}/${chapterId}`);
  return response.data;
}

export interface ReadingStats {
  total_seconds: number;
  today_seconds: number;
  read_chapters: number;
  total_chapters: number;
  progress_pct: number;
  total_words: number;
  avg_wpm: number;
  remaining_minutes: number;
}

export async function getReadingStats(bookId: number): Promise<ReadingStats> {
  const response = await apiClient.get(`/api/reading/stats/${bookId}`);
  return response.data;
}

export interface TodayStats {
  today_seconds: number;
  today_books: number;
  today_chapters: number;
}

export async function getTodayStats(): Promise<TodayStats> {
  const response = await apiClient.get("/api/reading/today");
  return response.data;
}
