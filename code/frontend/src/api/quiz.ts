/**
 * 陪练 API 客户端
 *
 * 提供章节测验、全书考试的接口。
 */
import apiClient from "./client";

/** 题目 */
export interface QuizQuestion {
  type: "choice" | "true_false" | "short_answer";
  question: string;
  options?: string[];
  answer: string;
  explanation: string;
}

/** 评判结果 */
export interface JudgeResult {
  correct: boolean;
  explanation: string;
  current: number;
  total: number;
  correct_count?: number;
}

/** 测验返回结果 */
export interface QuizResult {
  questions: QuizQuestion[];
  total: number;
  mode: string;
}

/** 启动测验（超时 120 秒：章节测验或全书考试） */
export async function startQuiz(
  bookId: number,
  options: {
    chapter_id?: number | null;
    count?: number;
    mode?: string;
  } = {}
): Promise<QuizResult> {
  const { chapter_id = null, count = 5, mode = chapter_id ? "chapter" : "exam" } = options;
  const response = await apiClient.post(
    `/api/quiz/${bookId}/start`,
    { chapter_id, count, mode },
    { timeout: 120000 }
  );
  return response.data;
}

/** 提交答案并评判（超时 120 秒） */
export async function submitAnswer(
  bookId: number,
  question: QuizQuestion,
  answer: string
): Promise<JudgeResult> {
  const response = await apiClient.post(
    `/api/quiz/${bookId}/answer`,
    { question, answer },
    { timeout: 120000 }
  );
  return response.data;
}

/** 获取下一题 */
export async function getNextQuestion(
  bookId: number
): Promise<{ question?: QuizQuestion; done?: boolean; correct?: number; total?: number }> {
  const response = await apiClient.get(`/api/quiz/${bookId}/next`);
  return response.data;
}

/** 查询测验进度 */
export async function getQuizProgress(bookId: number): Promise<Record<string, unknown>> {
  const response = await apiClient.get(`/api/quiz/${bookId}/progress`);
  return response.data;
}
