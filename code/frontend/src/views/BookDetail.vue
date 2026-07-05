<!--
  书籍详情页
  左侧章节树，右侧内容区 + 高亮功能
-->
<script setup lang="ts">
import { onMounted, onUnmounted, ref, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getBook, getChapters, getChapterContent } from "../api/books";
import { getChapterHighlights, createHighlight, deleteHighlight } from "../api/highlights";
import { startReading, stopReading, getReadingStats } from "../api/reading";
import type { ReadingStats } from "../api/reading";
import type { BookItem, ChapterNode, ChapterContent } from "../api/books";
import type { HighlightItem } from "../api/highlights";

const route = useRoute();
const router = useRouter();
const bookId = Number(route.params.id);

const book = ref<BookItem | null>(null);
const chapters = ref<ChapterNode[]>([]);
const currentChapter = ref<ChapterContent | null>(null);
const highlights = ref<HighlightItem[]>([]);
const loading = ref(true);
const contentRef = ref<HTMLElement | null>(null);
const readingStats = ref<ReadingStats | null>(null);

// 高亮弹出工具栏
const showToolbar = ref(false);
const toolbarPos = ref({ x: 0, y: 0 });
const selectedText = ref("");
const selectedColor = ref("yellow");

const colors = [
  { value: "yellow", label: "黄", bg: "#fff9c4" },
  { value: "green", label: "绿", bg: "#c8e6c9" },
  { value: "blue", label: "蓝", bg: "#bbdefb" },
  { value: "pink", label: "粉", bg: "#f8bbd0" },
];

function goBack() {
  router.push("/books");
}

async function loadBook() {
  loading.value = true;
  try {
    book.value = await getBook(bookId);
    chapters.value = await getChapters(bookId);
    // 加载阅读统计
    getReadingStats(bookId).then(s => { readingStats.value = s; }).catch(() => {});
  } finally {
    loading.value = false;
  }
}

async function selectChapter(chapterId: number) {
  // 停止上一章的阅读计时，并刷新进度
  if (selectedChapterId.value) {
    await stopReading(bookId, selectedChapterId.value).catch(() => {});
    // 刷新阅读统计
    getReadingStats(bookId).then(s => { readingStats.value = s; }).catch(() => {});
  }

  try {
    const content = await getChapterContent(bookId, chapterId);
    currentChapter.value = content;
    selectedChapterId.value = chapterId;

    // 开始新章节的阅读计时
    startReading(bookId, chapterId).catch(() => {});

    // 加载该章节的高亮
    const hl = await getChapterHighlights(bookId, chapterId);
    highlights.value = hl.highlights;

    // 等 DOM 更新后应用高亮
    await nextTick();
    applyHighlights();
  } catch {
    alert("加载章节内容失败");
  }
}

// 当前选中的章节 ID，用于高亮
const selectedChapterId = ref<number | null>(null);

/** 文本选中事件 */
function onTextSelect() {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed || !selection.toString().trim()) {
    showToolbar.value = false;
    return;
  }

  const text = selection.toString().trim();
  if (text.length < 2 || text.length > 500) {
    showToolbar.value = false;
    return;
  }

  selectedText.value = text;

  // 计算工具栏位置
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  const container = contentRef.value;
  if (container) {
    const containerRect = container.getBoundingClientRect();
    toolbarPos.value = {
      x: rect.left - containerRect.left + rect.width / 2,
      y: rect.top - containerRect.top - 40,
    };
  }

  showToolbar.value = true;
}

/** 创建高亮 */
async function addHighlight() {
  if (!selectedChapterId.value || !selectedText.value) return;

  try {
    await createHighlight(bookId, selectedChapterId.value, selectedText.value, selectedColor.value);
    // 刷新高亮
    const hl = await getChapterHighlights(bookId, selectedChapterId.value);
    highlights.value = hl.highlights;
    showToolbar.value = false;
    window.getSelection()?.removeAllRanges();

    // 重新应用高亮
    await nextTick();
    applyHighlights();
  } catch (e) {
    alert("高亮失败");
  }
}

/** 删除高亮 */
async function removeHighlight(hlId: number) {
  try {
    await deleteHighlight(hlId);
    highlights.value = highlights.value.filter((h) => h.id !== hlId);
    applyHighlights();
  } catch {
    alert("删除失败");
  }
}

/** 在内容区应用高亮样式 */
function applyHighlights() {
  const contentEl = contentRef.value;
  if (!contentEl || !currentChapter.value) return;

  const textNodes = getTextNodes(contentEl);
  for (const hl of highlights.value) {
    let remaining = hl.text;
    for (const node of textNodes) {
      if (!remaining) break;
      const idx = node.textContent?.indexOf(remaining) ?? -1;
      if (idx >= 0) {
        const parent = node.parentElement;
        if (parent) {
          const range = document.createRange();
          range.setStart(node, idx);
          range.setEnd(node, idx + remaining.length);
          const span = document.createElement("span");
          span.style.backgroundColor = hl.color === "yellow" ? "#fff9c4"
            : hl.color === "green" ? "#c8e6c9"
            : hl.color === "blue" ? "#bbdefb"
            : "#f8bbd0";
          span.style.borderRadius = "2px";
          span.style.cursor = "pointer";
          span.title = hl.note || "点击删除";
          span.onclick = () => removeHighlight(hl.id);
          range.surroundContents(span);
          remaining = "";
        }
      }
    }
  }
}

/** 获取所有文本节点 */
function getTextNodes(el: HTMLElement): Text[] {
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
  const nodes: Text[] = [];
  while (walker.nextNode()) {
    nodes.push(walker.currentNode as Text);
  }
  return nodes;
}

/** 缩进样式 */
function indentStyle(level: number) {
  return { paddingLeft: `${16 + (level - 1) * 20}px` };
}

onMounted(loadBook);

// 离开页面时停止阅读计时
onUnmounted(async () => {
  if (selectedChapterId.value) {
    await stopReading(bookId, selectedChapterId.value).catch(() => {});
  }
});
</script>

<template>
  <div class="book-detail">
    <!-- 左侧章节树 -->
    <aside class="chapter-tree">
      <div class="tree-header">
        <button class="btn-back" @click="goBack">← 返回</button>
        <h3>目录</h3>
      </div>
      <!-- 阅读进度 -->
      <div v-if="readingStats" class="reading-progress">
        <div class="progress-row">
          <span class="progress-label">阅读进度</span>
          <span class="progress-pct">{{ readingStats.progress_pct }}%</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" :style="{ width: readingStats.progress_pct + '%' }"></div>
        </div>
        <div class="progress-detail">
          {{ readingStats.read_chapters }}/{{ readingStats.total_chapters }}章 ·
          已读{{ Math.floor(readingStats.total_seconds / 60) }}分钟 ·
          均速{{ readingStats.avg_wpm }}字/分
        </div>
      </div>
      <div v-if="chapters.length === 0" class="tree-empty">暂无章节</div>
      <div v-else class="tree-list">
        <div
          v-for="ch in chapters"
          :key="ch.id"
          class="tree-item"
          :class="{ active: selectedChapterId === ch.id }"
          :style="indentStyle(ch.level)"
          @click="selectChapter(ch.id)"
        >
          <span class="tree-title">{{ ch.title }}</span>
          <span v-if="ch.word_count" class="tree-words">{{ ch.word_count }} 字</span>
        </div>
      </div>
    </aside>

    <!-- 右侧内容区 -->
    <main class="chapter-content" ref="contentRef" @mouseup="onTextSelect">
      <div v-if="loading" class="content-loading">加载中...</div>
      <div v-else-if="!currentChapter" class="content-hint">请从左侧选择要阅读的章节</div>
      <div v-else class="content-body">
        <h2 class="content-title">{{ currentChapter.title }}</h2>
        <div class="content-text" v-text="currentChapter.content"></div>
      </div>

      <!-- 高亮弹出工具栏 -->
      <div
        v-if="showToolbar"
        class="hl-toolbar"
        :style="{ left: toolbarPos.x + 'px', top: toolbarPos.y + 'px' }"
      >
        <div class="hl-colors">
          <button
            v-for="c in colors"
            :key="c.value"
            class="hl-color-btn"
            :style="{ background: c.bg, border: selectedColor === c.value ? '2px solid #333' : '2px solid transparent' }"
            :title="c.label"
            @click="selectedColor = c.value"
          ></button>
        </div>
        <button class="hl-confirm" @click="addHighlight">高亮</button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.book-detail {
  display: flex;
  height: calc(100vh - 80px);
  gap: 0;
  margin: -24px;
}

/* 左侧章节树 */
.chapter-tree {
  width: 280px;
  border-right: 1px solid #eee;
  overflow-y: auto;
  padding: 0;
  background: #fafafa;
  flex-shrink: 0;
}

.tree-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  background: #fafafa;
  z-index: 1;
}

.btn-back {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 13px;
  padding: 2px 6px;
  border-radius: 4px;
}

.btn-back:hover { background: #e8e8f0; color: #1a1a2e; }

.tree-header h3 { font-size: 15px; color: #1a1a2e; }

.reading-progress {
  padding: 10px 16px;
  border-bottom: 1px solid #eee;
  font-size: 12px;
}

.progress-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.progress-label { color: #888; }
.progress-pct { color: #1a1a2e; font-weight: 600; }

.progress-bar-bg {
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  margin-bottom: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: #1a1a2e;
  border-radius: 2px;
  transition: width 0.5s;
}

.progress-detail { color: #bbb; font-size: 11px; }
.tree-empty { padding: 24px 16px; color: #999; text-align: center; font-size: 13px; }

.tree-item {
  padding: 8px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #555;
  transition: background 0.15s;
}

.tree-item:hover { background: #eef; }
.tree-item.active { background: #dde; color: #1a1a2e; font-weight: 500; }

.tree-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-words { font-size: 11px; color: #bbb; margin-left: 8px; flex-shrink: 0; }

/* 右侧内容区 */
.chapter-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 40px;
  position: relative;
}

.content-loading, .content-hint {
  text-align: center;
  padding: 60px;
  color: #999;
  font-size: 14px;
}

.content-title {
  font-size: 22px;
  color: #1a1a2e;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.content-text {
  font-size: 15px;
  line-height: 2;
  color: #333;
  white-space: pre-wrap;
  user-select: text;
}

/* 高亮工具栏 */
.hl-toolbar {
  position: absolute;
  transform: translate(-50%, -100%);
  display: flex;
  align-items: center;
  gap: 6px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 6px 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
  z-index: 100;
}

.hl-colors {
  display: flex;
  gap: 4px;
}

.hl-color-btn {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  padding: 0;
}

.hl-confirm {
  padding: 4px 10px;
  background: #1a1a2e;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
</style>
