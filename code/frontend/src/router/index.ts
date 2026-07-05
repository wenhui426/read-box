/**
 * 前端路由配置
 *
 * 使用 Vue Router 的 Hash 模式（#/path），
 * 因为 Tauri 使用文件协议加载前端，History 模式会导致 404。
 *
 * 路由清单：
 * - /            → 首页欢迎页
 * - /books       → 书籍管理列表
 * - /books/:id   → 书籍详情（章节树 + 阅读）
 * - /books/:id/digest  → AI 提炼结果
 * - /books/:id/chat    → 问答对话
 * - /settings    → LLM 配置
 */
import { createRouter, createWebHashHistory } from "vue-router";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", name: "home", component: () => import("../views/Home.vue") },
    { path: "/books", name: "books", component: () => import("../views/BookList.vue") },
    { path: "/books/:id", name: "book-detail", component: () => import("../views/BookDetail.vue") },
    { path: "/books/:id/digest", name: "book-digest", component: () => import("../views/BookDigest.vue") },
    { path: "/books/:id/chat", name: "book-chat", component: () => import("../views/ChatView.vue") },
    { path: "/books/:id/quiz", name: "book-quiz", component: () => import("../views/QuizView.vue") },
    { path: "/settings", name: "settings", component: () => import("../views/SettingsView.vue") },
  ],
});

export default router;
