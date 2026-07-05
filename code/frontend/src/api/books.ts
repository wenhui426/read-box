/**
 * 书籍管理 API
 *
 * 提供导入、查询、删除书籍的接口方法。
 * 后端地址由全局配置自动获取。
 */

import apiClient from "./client";

/** 书籍条目 */
export interface BookItem {
  id: number;
  title: string;
  author: string;
  file_type: string;
  status: string;
  total_chapters: number;
  total_words: number;
  created_at: string;
}

/** 章节节点 */
export interface ChapterNode {
  id: number;
  parent_id: number | null;
  title: string;
  level: number;
  sort_order: number;
  page_number: number | null;
  word_count: number;
}

/** 章节内容 */
export interface ChapterContent {
  id: number;
  title: string;
  content: string;
  word_count: number;
}

/** 导入书籍（超时 60 秒，大 PDF 上传较慢） */
export async function importBook(file: File): Promise<{ book_id: number; status: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post("/api/books/import", formData, {
    timeout: 60000,
  });
  return response.data;
}

/** 获取书籍列表 */
export async function getBooks(): Promise<BookItem[]> {
  const response = await apiClient.get("/api/books");
  return response.data;
}

/** 获取单本书详情 */
export async function getBook(bookId: number): Promise<BookItem> {
  const response = await apiClient.get(`/api/books/${bookId}`);
  return response.data;
}

/** 获取章节树 */
export async function getChapters(bookId: number): Promise<ChapterNode[]> {
  const response = await apiClient.get(`/api/books/${bookId}/chapters`);
  return response.data;
}

/** 获取章节内容 */
export async function getChapterContent(
  bookId: number,
  chapterId: number
): Promise<ChapterContent> {
  const response = await apiClient.get(
    `/api/books/${bookId}/chapters/${chapterId}`
  );
  return response.data;
}

/** 删除书籍 */
export async function deleteBook(bookId: number): Promise<void> {
  await apiClient.delete(`/api/books/${bookId}`);
}
