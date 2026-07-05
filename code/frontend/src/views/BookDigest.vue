<!--
  书籍提炼结果页

  展示全书 AI 提炼结果：
  - 顶部：进度条 + 提炼控制按钮
  - 中部：章节摘要卡片列表
  - 每张卡片：摘要、关键概念、金句摘录
  - 底部：导出 Markdown 按钮
-->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import {
  startDigest,
  getDigestStatus,
  getChapterDigest,
  exportDigest,
} from "../api/digest";
import { getChapters } from "../api/books";
import type { ChapterNode } from "../api/books";
import type { ChapterDigestResult } from "../api/digest";

const route = useRoute();
const bookId = Number(route.params.id);

const digesting = ref(false);
const progress = ref({ processed: 0, total: 0 });
const chapters = ref<ChapterNode[]>([]);
const results = ref<Record<number, ChapterDigestResult>>({});
const polling = ref<ReturnType<typeof setInterval> | null>(null);

/** 加载章节列表 */
async function loadChapters() {
  chapters.value = await getChapters(bookId);
}

/** 启动全书提炼 */
async function handleStartDigest() {
  digesting.value = true;
  await startDigest(bookId);
  // 开始轮询进度
  polling.value = setInterval(pollProgress, 2000);
}

/** 轮询提炼进度 */
async function pollProgress() {
  const status = await getDigestStatus(bookId);
  progress.value = { processed: status.processed, total: status.total };

  // 加载已完成章节的结果
  if (chapters.value.length > 0) {
    for (const ch of chapters.value) {
      if (!results.value[ch.id]) {
        try {
          const result = await getChapterDigest(bookId, ch.id);
          if (result.summary) {
            results.value[ch.id] = result;
          }
        } catch {
          // 章节尚未完成提炼
        }
      }
    }
  }

  // 检查是否完成
  if (status.status === "completed" || status.processed >= status.total) {
    if (polling.value) {
      clearInterval(polling.value);
      polling.value = null;
    }
    digesting.value = false;
    // 最后再加载一次所有结果
    await loadAllResults();
  }
}

/** 加载全部提炼结果 */
async function loadAllResults() {
  for (const ch of chapters.value) {
    if (!results.value[ch.id]) {
      try {
        const result = await getChapterDigest(bookId, ch.id);
        if (result.summary) {
          results.value[ch.id] = result;
        }
      } catch {
        // 忽略无结果
      }
    }
  }
}

/** 导出 Markdown */
async function handleExport() {
  try {
    const blob = await exportDigest(bookId);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `读书笔记_${bookId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  } catch {
    alert("导出失败");
  }
}

onMounted(async () => {
  await loadChapters();
  // 检查是否有进行中的提炼任务
  const status = await getDigestStatus(bookId);
  if (status.status === "processing") {
    digesting.value = true;
    progress.value = { processed: status.processed, total: status.total };
    polling.value = setInterval(pollProgress, 2000);
  } else if (status.status === "completed") {
    await loadAllResults();
  }
});
</script>

<template>
  <div class="digest-page">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <h2>AI 提炼</h2>
      <div class="actions">
        <button
          v-if="!digesting && Object.keys(results).length > 0"
          class="btn-secondary"
          @click="handleExport"
        >
          导出 Markdown
        </button>
        <button
          class="btn-primary"
          :disabled="digesting"
          @click="handleStartDigest"
        >
          {{ digesting ? "提炼中..." : "提炼全书" }}
        </button>
      </div>
    </div>

    <!-- 进度条 -->
    <div v-if="digesting" class="progress-bar">
      <div class="progress-fill" :style="{ width: progress.total > 0 ? (progress.processed / progress.total * 100) + '%' : '0%' }"></div>
      <span class="progress-text">{{ progress.processed }} / {{ progress.total }} 章</span>
    </div>

    <!-- 无结果提示 -->
    <div v-if="!digesting && Object.keys(results).length === 0" class="empty">
      <p>还未进行提炼</p>
      <p class="hint">点击"提炼全书"按钮，AI 将逐章生成摘要、概念和金句</p>
    </div>

    <!-- 提炼结果列表 -->
    <div v-if="Object.keys(results).length > 0" class="results">
      <div
        v-for="ch in chapters"
        :key="ch.id"
        class="chapter-card"
      >
        <!-- 仅在结果存在时显示 -->
        <template v-if="results[ch.id]">
          <h3 class="chapter-title">{{ ch.title }}</h3>

          <!-- 摘要 -->
          <div class="section">
            <h4>摘要</h4>
            <p class="summary-text">{{ results[ch.id].summary }}</p>
          </div>

          <!-- 关键概念 -->
          <div v-if="results[ch.id].concepts.length > 0" class="section">
            <h4>关键概念</h4>
            <ul class="concept-list">
              <li v-for="(c, i) in results[ch.id].concepts" :key="i">
                <strong>{{ c.term }}</strong>：{{ c.explanation }}
              </li>
            </ul>
          </div>

          <!-- 金句 -->
          <div v-if="results[ch.id].quotes.length > 0" class="section">
            <h4>金句摘录</h4>
            <blockquote
              v-for="(q, i) in results[ch.id].quotes"
              :key="i"
              class="quote-block"
            >
              <p>"{{ q.quote }}"</p>
              <footer>— {{ q.reason }}</footer>
            </blockquote>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.digest-page {
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.actions {
  display: flex;
  gap: 8px;
}

.progress-bar {
  position: relative;
  height: 32px;
  background: #eee;
  border-radius: 16px;
  margin-bottom: 24px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #1a1a2e;
  border-radius: 16px;
  transition: width 0.5s;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 13px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.empty {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.hint {
  font-size: 13px;
  margin-top: 8px;
  color: #ccc;
}

.results {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chapter-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.chapter-title {
  font-size: 17px;
  color: #1a1a2e;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.section {
  margin-bottom: 16px;
}

.section h4 {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.summary-text {
  font-size: 14px;
  line-height: 1.7;
  color: #444;
}

.concept-list {
  list-style: none;
  padding: 0;
}

.concept-list li {
  padding: 6px 0;
  font-size: 14px;
  color: #555;
}

.concept-list li::before {
  content: "•";
  color: #1a1a2e;
  font-weight: bold;
  margin-right: 8px;
}

.quote-block {
  margin: 12px 0;
  padding: 12px 16px;
  background: #f8f9fa;
  border-left: 3px solid #1a1a2e;
  border-radius: 4px;
}

.quote-block p {
  font-style: italic;
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

.quote-block footer {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}
</style>
