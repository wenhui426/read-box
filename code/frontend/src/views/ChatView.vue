<!--
  问答页面

  基于当前书籍的 AI 对话界面。
  支持流式输出、消息历史、上下文追问。
-->
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";
import { askQuestionStream, clearContext, getHistory } from "../api/qa";
import type { ChatMessage } from "../api/qa";

/** 简单的 Markdown 渲染（支持 **加粗**、*斜体*、`代码`、换行） */
function renderMarkdown(text: string): string {
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code style='background:#f0f0f0;padding:1px 4px;border-radius:3px;font-size:13px'>$1</code>")
    .replace(/\n/g, "<br>");
  return html;
}

const route = useRoute();
const bookId = Number(route.params.id);

const messages = ref<ChatMessage[]>([]);
const question = ref("");
const sending = ref(false);
const streamingContent = ref("");
const controller = ref<AbortController | null>(null);

/** 发送提问 */
async function sendQuestion() {
  const q = question.value.trim();
  if (!q || sending.value) return;

  question.value = "";
  sending.value = true;

  // 添加用户消息
  messages.value.push({ role: "user", content: q });
  streamingContent.value = "";

  // 发起流式请求
  controller.value = askQuestionStream(
    bookId,
    q,
    (chunk) => {
      streamingContent.value += chunk;
    },
    () => {
      // 流式完成，整条消息加入历史
      messages.value.push({ role: "assistant", content: streamingContent.value });
      streamingContent.value = "";
      sending.value = false;
      controller.value = null;
    },
    (err) => {
      messages.value.push({ role: "assistant", content: `错误：${err.message}` });
      sending.value = false;
      controller.value = null;
    }
  );
}

/** 清空对话 */
async function handleClear() {
  if (controller.value) {
    controller.value.abort();
    controller.value = null;
  }
  await clearContext(bookId);
  messages.value = [];
  streamingContent.value = "";
  sending.value = false;
}

/** 回车发送 */
function onKeyEnter() {
  sendQuestion();
}

onMounted(async () => {
  // 加载历史消息
  try {
    const history = await getHistory(bookId);
    if (history.history) {
      messages.value = history.history;
    }
  } catch {
    // 无历史
  }
});

onUnmounted(() => {
  if (controller.value) {
    controller.value.abort();
  }
});
</script>

<template>
  <div class="chat-page">
    <!-- 对话消息列表 -->
    <div class="message-list" ref="messageList">
      <div v-if="messages.length === 0 && !streamingContent" class="welcome">
        <h3>开始提问</h3>
        <p>输入你对这本书的疑问，AI 将基于书中内容回答</p>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="message"
        :class="msg.role"
      >
        <div class="bubble" v-html="renderMarkdown(msg.content)"></div>
      </div>

      <!-- 流式输出中的消息 -->
      <div v-if="streamingContent" class="message assistant">
        <div class="bubble typing" v-html="renderMarkdown(streamingContent)"></div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <button class="btn-clear" @click="handleClear" title="清空对话">🗑</button>
      <input
        v-model="question"
        type="text"
        placeholder="输入你对这本书的疑问..."
        :disabled="sending"
        @keyup.enter="onKeyEnter"
      />
      <button
        class="btn-send"
        :disabled="sending || !question.trim()"
        @click="sendQuestion"
      >
        {{ sending ? "..." : "发送" }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  max-width: 800px;
  margin: 0 auto;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.welcome h3 {
  font-size: 18px;
  color: #666;
  margin-bottom: 8px;
}

.message {
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 75%;
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message.user .bubble {
  background: #1a1a2e;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .bubble {
  background: #f0f0f5;
  color: #333;
  border-bottom-left-radius: 4px;
}

.typing::after {
  content: "▌";
  animation: blink 0.8s infinite;
}

@keyframes blink {
  50% { opacity: 0; }
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 12px 0;
  border-top: 1px solid #eee;
}

.input-area input {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.input-area input:focus {
  border-color: #1a1a2e;
}

.btn-clear {
  background: none;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 16px;
}

.btn-send {
  padding: 10px 24px;
  background: #1a1a2e;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
