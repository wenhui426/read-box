/**
 * 首页数据 API 客户端
 */
import apiClient from "./client";

export interface DashboardBook {
  id: number;
  title: string;
  author: string;
  file_type: string;
  total_chapters: number;
  total_words: number;
  created_at: string;
}

export interface DashboardData {
  recent_books: DashboardBook[];
  total_books: number;
  pending_digest_count: number;
}

export async function getDashboard(): Promise<DashboardData> {
  const response = await apiClient.get("/api/dashboard");
  return response.data;
}
