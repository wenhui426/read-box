<!--
  首页：精致版
  - 渐变头部 + 快捷操作
  - 最近阅读卡片
  - 统计网格
  - 待办提醒
-->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAppStore } from "../stores/app";
import { getDashboard } from "../api/dashboard";
import { getTodayStats } from "../api/reading";
import type { DashboardBook } from "../api/dashboard";

const router = useRouter();
const appStore = useAppStore();

const recentBooks = ref<DashboardBook[]>([]);
const totalBooks = ref(0);
const pendingDigest = ref(0);
const todaySeconds = ref(0);
const todayChapters = ref(0);

function goTo(path: string) {
  router.push(path);
}

onMounted(async () => {
  appStore.checkBackendStatus();
  try {
    const [data, today] = await Promise.all([
      getDashboard(),
      getTodayStats().catch(() => ({ today_seconds: 0, today_books: 0, today_chapters: 0 })),
    ]);
    recentBooks.value = data.recent_books;
    totalBooks.value = data.total_books;
    pendingDigest.value = data.pending_digest_count;
    todaySeconds.value = today.today_seconds;
    todayChapters.value = today.today_chapters;
  } catch {}
});
</script>

<template>
  <div class="home">
    <!-- 标题头部 -->
    <div class="hero">
      <div class="hero-content">
        <div class="hero-icon">📚</div>
        <h1 class="hero-title">Read-Box</h1>
        <p class="hero-desc">本地桌面读书辅助系统</p>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <button class="action-card" @click="goTo('/books')">
        <span class="action-icon">📖</span>
        <span class="action-label">管理书籍</span>
      </button>
      <button class="action-card" @click="goTo('/books')">
        <span class="action-icon">➕</span>
        <span class="action-label">导入书籍</span>
      </button>
      <button class="action-card" @click="goTo('/settings')">
        <span class="action-icon">⚙️</span>
        <span class="action-label">模型配置</span>
      </button>
    </div>

    <!-- 待办提醒 -->
    <div v-if="pendingDigest > 0" class="alert-banner" @click="goTo('/books')">
      <span class="alert-icon">📋</span>
      <span>有 {{ pendingDigest }} 个提炼任务待处理</span>
      <span class="alert-arrow">→</span>
    </div>

    <!-- 最近阅读 -->
    <section class="section-card">
      <div class="section-header">
        <h2>📖 最近阅读</h2>
        <a v-if="totalBooks > 0" @click="goTo('/books')" class="more-link">查看全部 →</a>
      </div>
      <div v-if="recentBooks.length === 0" class="empty-state">
        <div class="empty-icon">📖</div>
        <p>还没有导入书籍</p>
        <button class="btn-primary" @click="goTo('/books')">导入第一本书</button>
      </div>
      <div v-else class="book-scroll">
        <div
          v-for="book in recentBooks"
          :key="book.id"
          class="book-card"
          @click="goTo(`/books/${book.id}`)"
        >
          <div class="book-emoji">{{ book.file_type === 'pdf' ? '📕' : '📘' }}</div>
          <div class="book-title">{{ book.title }}</div>
          <div class="book-meta">{{ book.total_chapters }} 章 · {{ (book.total_words / 1000).toFixed(1) }}k 字</div>
        </div>
      </div>
    </section>

    <!-- 统计网格 -->
    <section class="section stats-section">
      <h2>阅读统计</h2>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ totalBooks }}</div>
          <div class="stat-label">📚 已导入书籍</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ (totalBooks > 0 ? recentBooks.reduce((s, b) => s + b.total_words, 0) : 0).toLocaleString() }}</div>
          <div class="stat-label">📝 总字数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ Math.floor(todaySeconds / 60) }}</div>
          <div class="stat-label">⏱️ 今日阅读(分钟)</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ todayChapters }}</div>
          <div class="stat-label">📑 今日章节</div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 0 40px;
}

/* ===== 标题头部 ===== */
.hero {
  text-align: center;
  padding: 32px 20px 16px;
}

.hero-icon {
  font-size: 34px;
  margin-bottom: 6px;
  line-height: 1;
}

.hero-title {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}

.hero-desc {
  font-size: 13px;
  color: #bbb;
}

/* ===== 快捷操作 ===== */
.quick-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.action-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 8px;
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.action-card:hover {
  border-color: #1a1a2e;
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(26, 26, 46, 0.1);
}

.action-icon { font-size: 22px; }
.action-label { font-size: 13px; color: #555; font-weight: 500; }

/* ===== 提醒 ===== */
.alert-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fff8e1, #fff3cd);
  border: 1px solid #ffe082;
  border-radius: 10px;
  font-size: 13px;
  color: #e65100;
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.2s;
}

.alert-banner:hover { transform: translateX(4px); }
.alert-arrow { margin-left: auto; font-weight: bold; }

/* ===== 区块 ===== */
.section { margin-bottom: 28px; }

/* 卡片式区块 */
.section-card {
  background: white;
  border-radius: 14px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.section h2 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.more-link {
  font-size: 13px;
  color: #1a1a2e;
  cursor: pointer;
  font-weight: 500;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.more-link:hover { opacity: 1; }

/* ===== 空状态 ===== */
.empty-state {
  text-align: center;
  padding: 36px 20px;
  background: #fafafa;
  border-radius: 10px;
  border: 1px dashed #ddd;
}

.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state p { color: #999; font-size: 14px; margin-bottom: 16px; }

.btn-primary {
  padding: 10px 28px;
  background: #1a1a2e;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover { background: #2a2a4e; }

/* ===== 书籍卡片滚动 ===== */
.book-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: thin;
}

.book-card {
  flex: 0 0 150px;
  background: white;
  border-radius: 12px;
  padding: 20px 14px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 1px solid #f0f0f0;
}

.book-card:hover {
  border-color: #d0d0e0;
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
}

.book-emoji { font-size: 36px; margin-bottom: 10px; line-height: 1; }
.book-title { font-size: 13px; font-weight: 600; color: #1a1a2e; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.book-meta { font-size: 11px; color: #bbb; }

/* ===== 统计 ===== */
.stats-section {
  background: white;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.stats-section h2 {
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 12px;
}

.stat-card {
  text-align: center;
  padding: 18px 8px 14px;
  border-radius: 10px;
  background: #f8f8fa;
  transition: all 0.2s;
}

.stat-card:hover {
  background: #f0f0f5;
  transform: translateY(-2px);
}

.stat-value { font-size: 22px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
.stat-label { font-size: 12px; color: #999; }
</style>
