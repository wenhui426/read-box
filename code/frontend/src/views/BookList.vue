<!--
  书籍列表页

  展示所有已导入的书籍，提供导入新书和查看详情的入口。
-->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getBooks, importBook, deleteBook } from "../api/books";
import type { BookItem } from "../api/books";

const router = useRouter();
const books = ref<BookItem[]>([]);
const loading = ref(false);
const importing = ref(false);

/** 加载书籍列表 */
async function loadBooks() {
  loading.value = true;
  try {
    books.value = await getBooks();
  } finally {
    loading.value = false;
  }
}

/** 导入新书 */
async function handleImport() {
  // 创建隐藏的文件选择器
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".pdf,.epub,.txt";
  input.onchange = async () => {
    const file = input.files?.[0];
    if (!file) return;

    importing.value = true;
    try {
      await importBook(file);
      await loadBooks();
    } catch (e) {
      // 显示后端返回的具体错误原因（如"扫描版无文本层"）
      const err = e as { response?: { data?: { detail?: string } }; message?: string };
      const detail = err.response?.data?.detail || err.message || "未知错误";
      alert("导入失败：" + detail);
    } finally {
      importing.value = false;
    }
  };
  input.click();
}

/** 删除书籍 */
async function handleDelete(bookId: number, title: string) {
  if (!confirm(`确定要删除"${title}"吗？`)) return;
  try {
    await deleteBook(bookId);
    await loadBooks();
  } catch (e) {
    alert("删除失败");
  }
}

/** 点击书籍进入详情 */
function viewBook(bookId: number) {
  router.push(`/books/${bookId}`);
}

onMounted(loadBooks);
</script>

<template>
  <div class="book-list-page">
    <!-- 页面标题与操作栏 -->
    <div class="page-header">
      <h2>我的书籍</h2>
      <button class="btn-primary" :disabled="importing" @click="handleImport">
        {{ importing ? "导入中..." : "+ 导入书籍" }}
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 空状态 -->
    <div v-else-if="books.length === 0" class="empty-state">
      <p>还没有导入任何书籍</p>
      <p class="hint">点击上方"导入书籍"按钮开始</p>
    </div>

    <!-- 书籍列表 -->
    <div v-else class="book-grid">
      <div
        v-for="book in books"
        :key="book.id"
        class="book-card"
        @click="viewBook(book.id)"
      >
        <div class="book-info">
          <h3 class="book-title">{{ book.title }}</h3>
          <p class="book-meta">
            {{ book.author || "未知作者" }}
            <span class="tag">{{ book.file_type.toUpperCase() }}</span>
          </p>
          <p class="book-stats">
            {{ book.total_chapters }} 章 · {{ book.total_words }} 字
          </p>
        </div>
        <div class="book-status">
          <span v-if="book.status === 'completed'" class="status-completed"
            >已解析</span
          >
          <span v-else-if="book.status === 'parsing'" class="status-parsing"
            >解析中</span
          >
          <span v-else class="status-failed">失败</span>
        </div>
        <button
          class="btn-delete"
          @click.stop="handleDelete(book.id, book.title)"
        >
          删除
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.book-list-page {
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 22px;
  color: #1a1a2e;
}

.btn-primary {
  padding: 8px 20px;
  background: #1a1a2e;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.hint {
  font-size: 13px;
  margin-top: 8px;
  color: #999;
}

.book-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.book-card {
  display: flex;
  align-items: center;
  background: white;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.book-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.book-info {
  flex: 1;
}

.book-title {
  font-size: 16px;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.book-meta {
  font-size: 13px;
  color: #888;
}

.tag {
  display: inline-block;
  padding: 1px 6px;
  background: #eef;
  border-radius: 4px;
  font-size: 11px;
  margin-left: 6px;
}

.book-stats {
  font-size: 12px;
  color: #aaa;
  margin-top: 4px;
}

.book-status {
  margin: 0 16px;
}

.status-completed {
  color: #4caf50;
  font-size: 13px;
}
.status-parsing {
  color: #ff9800;
  font-size: 13px;
}
.status-failed {
  color: #f44336;
  font-size: 13px;
}

.btn-delete {
  padding: 4px 12px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  color: #999;
  cursor: pointer;
  font-size: 12px;
}

.btn-delete:hover {
  border-color: #f44336;
  color: #f44336;
}
</style>
