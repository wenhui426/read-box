/**
 * 高亮 API 客户端
 */
import apiClient from "./client";

export interface HighlightItem {
  id: number;
  chapter_id: number;
  text: string;
  color: string;
  note: string;
  created_at: string;
}

export async function getHighlights(bookId: number): Promise<{ highlights: HighlightItem[] }> {
  const response = await apiClient.get(`/api/highlights/${bookId}`);
  return response.data;
}

export async function getChapterHighlights(
  bookId: number,
  chapterId: number
): Promise<{ highlights: HighlightItem[] }> {
  const response = await apiClient.get(`/api/highlights/${bookId}/chapters/${chapterId}`);
  return response.data;
}

export async function createHighlight(
  bookId: number,
  chapterId: number,
  text: string,
  color: string = "yellow",
  note: string = ""
): Promise<{ id: number }> {
  const response = await apiClient.post(`/api/highlights/${bookId}/chapters/${chapterId}`, {
    text,
    color,
    note,
  });
  return response.data;
}

export async function updateHighlight(
  highlightId: number,
  data: { color?: string; note?: string }
): Promise<void> {
  await apiClient.put(`/api/highlights/${highlightId}`, data);
}

export async function deleteHighlight(highlightId: number): Promise<void> {
  await apiClient.delete(`/api/highlights/${highlightId}`);
}
