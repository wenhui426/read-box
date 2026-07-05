<!--
  陪练页面

  两种模式：
  - 章节测验：选择具体章节，AI 根据该章内容出题
  - 全书考试：综合全书内容出题
-->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { getChapters } from "../api/books";
import { startQuiz, submitAnswer } from "../api/quiz";
import type { ChapterNode } from "../api/books";
import type { QuizQuestion, JudgeResult } from "../api/quiz";

const route = useRoute();
const bookId = Number(route.params.id);

const chapters = ref<ChapterNode[]>([]);
const selectedChapterId = ref<number | null>(null);
const mode = ref<"chapter" | "exam">("chapter");
const questions = ref<QuizQuestion[]>([]);
const currentIndex = ref(0);
const userAnswer = ref("");
const judgeResult = ref<JudgeResult | null>(null);
const correctCount = ref(0);
const loading = ref(false);
const started = ref(false);
const finished = ref(false);

/** 加载章节列表 */
async function loadChapters() {
  chapters.value = await getChapters(bookId);
}

/** 启动测验 */
async function handleStart() {
  if (mode.value === "chapter" && !selectedChapterId.value) return;
  loading.value = true;
  try {
    const result = await startQuiz(bookId, {
      chapter_id: mode.value === "chapter" ? selectedChapterId.value : null,
      count: mode.value === "exam" ? 10 : 5,
      mode: mode.value,
    });
    questions.value = result.questions;
    currentIndex.value = 0;
    correctCount.value = 0;
    started.value = true;
    finished.value = false;
    judgeResult.value = null;
    userAnswer.value = "";
  } catch (e) {
    alert("出题失败：" + (e as Error).message);
  } finally {
    loading.value = false;
  }
}

/** 提交答案 */
async function handleSubmit() {
  const q = questions.value[currentIndex.value];
  if (!q || !userAnswer.value.trim()) return;
  loading.value = true;
  try {
    const result = await submitAnswer(bookId, q, userAnswer.value);
    judgeResult.value = result;
    if (result.correct) correctCount.value++;
  } catch {
    alert("提交失败");
  } finally {
    loading.value = false;
  }
}

/** 下一题 */
function nextQuestion() {
  const next = currentIndex.value + 1;
  if (next >= questions.value.length) {
    finished.value = true;
    return;
  }
  currentIndex.value = next;
  userAnswer.value = "";
  judgeResult.value = null;
}

/** 重新开始 */
function restart() {
  started.value = false;
  finished.value = false;
  questions.value = [];
  currentIndex.value = 0;
  judgeResult.value = null;
  userAnswer.value = "";
}

/** 选择章节 */
function selectChapter(id: number) {
  selectedChapterId.value = id;
  mode.value = "chapter";
  handleStart();
}

/** 全书考试 */
function startExam() {
  mode.value = "exam";
  selectedChapterId.value = null;
  handleStart();
}

onMounted(loadChapters);
</script>

<template>
  <div class="quiz-page">
    <!-- 模式选择和开始（未开始时） -->
    <div v-if="!started" class="quiz-start">
      <h2>{{ mode === "exam" ? "全书考试" : "章节测验" }}</h2>
      <p class="desc">
        {{ mode === "exam" ? "综合全书内容出题，测试你对整本书的掌握程度" : "选择一个章节，AI 根据该章内容出题" }}
      </p>

      <!-- 模式切换 -->
      <div class="mode-tabs">
        <button
          :class="['mode-tab', { active: mode === 'chapter' }]"
          @click="mode = 'chapter'"
        >📖 按章节</button>
        <button
          :class="['mode-tab', { active: mode === 'exam' }]"
          @click="mode = 'exam'"
        >📚 按全书</button>
      </div>

      <!-- 章节列表（仅按章节模式） -->
      <div v-if="mode === 'chapter'" class="chapter-list">
        <div
          v-for="ch in chapters"
          :key="ch.id"
          class="chapter-item"
          @click="selectChapter(ch.id)"
        >
          <span class="ch-title">{{ ch.title }}</span>
          <span class="ch-words">{{ ch.word_count }} 字</span>
        </div>
        <div v-if="chapters.length === 0" class="empty">当前书籍没有章节</div>
      </div>

      <!-- 全书考试启动按钮 -->
      <button
        v-if="mode === 'exam'"
        class="btn-start-exam"
        :disabled="loading"
        @click="startExam"
      >
        {{ loading ? "出题中..." : "开始考试" }}
      </button>
    </div>

    <!-- 答题中 -->
    <div v-else-if="!finished" class="quiz-playing">
      <div class="quiz-header">
        <span class="quiz-progress">第 {{ currentIndex + 1 }} / {{ questions.length }} 题</span>
        <span class="quiz-score">正确：{{ correctCount }}</span>
        <button class="btn-quit" @click="restart">退出</button>
      </div>

      <div class="question-card">
        <div class="question-type">
          {{ questions[currentIndex]?.type === "choice" ? "选择题" :
             questions[currentIndex]?.type === "true_false" ? "判断题" : "简答题" }}
        </div>
        <div class="question-text" v-if="questions[currentIndex]">
          {{ questions[currentIndex].question }}
        </div>

        <!-- 选择题 -->
        <div v-if="questions[currentIndex]?.type === 'choice' && questions[currentIndex]?.options" class="options-list">
          <label
            v-for="opt in questions[currentIndex].options"
            :key="opt"
            class="option-item"
            :class="{ selected: userAnswer === opt.charAt(0) }"
          >
            <input type="radio" :value="opt.charAt(0)" v-model="userAnswer" :disabled="!!judgeResult" />
            {{ opt }}
          </label>
        </div>

        <!-- 判断题 -->
        <div v-else-if="questions[currentIndex]?.type === 'true_false'" class="options-list">
          <label class="option-item" :class="{ selected: userAnswer === '对' }">
            <input type="radio" value="对" v-model="userAnswer" :disabled="!!judgeResult" /> 对
          </label>
          <label class="option-item" :class="{ selected: userAnswer === '错' }">
            <input type="radio" value="错" v-model="userAnswer" :disabled="!!judgeResult" /> 错
          </label>
        </div>

        <!-- 简答题 -->
        <div v-else class="short-answer">
          <textarea v-model="userAnswer" placeholder="输入你的答案..." :disabled="!!judgeResult" rows="3"></textarea>
        </div>

        <button v-if="!judgeResult" class="btn-submit" :disabled="loading || !userAnswer.trim()" @click="handleSubmit">
          {{ loading ? "评判中..." : "提交答案" }}
        </button>

        <div v-if="judgeResult" class="judge-result" :class="judgeResult.correct ? 'correct' : 'wrong'">
          <p class="judge-icon">{{ judgeResult.correct ? "✅" : "❌" }}</p>
          <p class="judge-text">{{ judgeResult.explanation }}</p>
        </div>

        <button v-if="judgeResult" class="btn-next" @click="nextQuestion">
          {{ currentIndex + 1 >= questions.length ? "查看成绩" : "下一题" }}
        </button>
      </div>
    </div>

    <!-- 完成页 -->
    <div v-else class="quiz-finished">
      <div class="result-card">
        <h2>{{ mode === "exam" ? "全书考试" : "章节测验" }}完成！</h2>
        <div class="score-circle">
          <span class="score-num">{{ correctCount }}</span>
          <span class="score-divide">/</span>
          <span class="score-total">{{ questions.length }}</span>
        </div>
        <p class="score-desc">
          {{ correctCount === questions.length ? "满分！太棒了！🎉" :
             correctCount >= questions.length / 2 ? "不错，继续加油！" :
             "需要多复习一下哦" }}
        </p>
        <button class="btn-restart" @click="restart">再来一次</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quiz-page {
  max-width: 640px;
  margin: 0 auto;
}

/* 开始页 */
.quiz-start h2 {
  font-size: 20px;
  color: #1a1a2e;
  margin-bottom: 6px;
}

.desc {
  font-size: 13px;
  color: #999;
  margin-bottom: 20px;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.mode-tab {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.mode-tab.active {
  border-color: #1a1a2e;
  background: #1a1a2e;
  color: white;
}

.mode-tab:not(.active):hover {
  border-color: #1a1a2e;
}

.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chapter-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.chapter-item:hover {
  background: #f0f0f8;
  transform: translateX(4px);
}

.ch-title { font-size: 14px; color: #333; }
.ch-words { font-size: 12px; color: #bbb; }
.empty { text-align: center; padding: 40px; color: #999; }

.btn-start-exam {
  width: 100%;
  padding: 14px;
  background: #1a1a2e;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}

.btn-start-exam:disabled { opacity: 0.5; }

/* 答题中 */
.quiz-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.quiz-progress { font-size: 14px; color: #333; font-weight: 500; }
.quiz-score { font-size: 13px; color: #4caf50; }
.btn-quit { margin-left: auto; background: none; border: 1px solid #ddd; padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; color: #999; }

.question-card {
  background: white;
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.question-type { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
.question-text { font-size: 16px; color: #1a1a2e; line-height: 1.6; margin-bottom: 20px; }

.options-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }

.option-item {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  border: 1px solid #e0e0e0; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.15s;
}
.option-item:hover { border-color: #1a1a2e; }
.option-item.selected { border-color: #1a1a2e; background: #f0f0f8; }

.short-answer textarea {
  width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px;
  font-size: 14px; resize: vertical; margin-bottom: 16px; box-sizing: border-box;
}

.btn-submit, .btn-next {
  width: 100%; padding: 12px; border: none; border-radius: 8px; font-size: 14px; cursor: pointer;
}
.btn-submit { background: #1a1a2e; color: white; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.judge-result { margin-top: 16px; padding: 16px; border-radius: 8px; text-align: center; }
.judge-result.correct { background: #f0fff0; border: 1px solid #c8e6c9; }
.judge-result.wrong { background: #fff0f0; border: 1px solid #ffcdd2; }
.judge-result.wrong .judge-text { color: #c62828; font-weight: 500; }
.judge-icon { font-size: 28px; margin-bottom: 8px; }
.judge-text { font-size: 14px; color: #555; line-height: 1.6; }

.btn-next { margin-top: 12px; background: #e8e8f0; color: #333; }
.btn-next:hover { background: #dddde8; }

/* 完成页 */
.quiz-finished { text-align: center; padding: 40px 0; }
.result-card { background: white; border-radius: 16px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
.result-card h2 { font-size: 22px; color: #1a1a2e; margin-bottom: 24px; }
.score-circle { margin-bottom: 16px; }
.score-num { font-size: 48px; font-weight: 700; color: #1a1a2e; }
.score-divide { font-size: 36px; color: #ccc; margin: 0 4px; }
.score-total { font-size: 36px; color: #999; }
.score-desc { font-size: 15px; color: #666; margin-bottom: 24px; }
.btn-restart { padding: 12px 40px; background: #1a1a2e; color: white; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; }
</style>
