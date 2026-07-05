<script setup lang="ts">
import { onMounted, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAppStore } from "./stores/app";

const router = useRouter();
const route = useRoute();
const appStore = useAppStore();

/** 当前书籍 ID（详情页/提炼页/问答页时使用） */
const currentBookId = computed(() => route.params.id as string);

/** 导航到书籍管理页 */
function goTo(path: string) {
  router.push(path);
}

onMounted(() => {
  appStore.checkBackendStatus();
});
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-left">
        <h1 @click="goTo('/')" style="cursor: pointer">Read-Box</h1>
        <nav class="nav-links">
          <a @click="goTo('/')">首页</a>
          <a @click="goTo('/books')">书籍管理</a>
          <a @click="goTo('/settings')">模型配置</a>
          <template v-if="currentBookId">
            <span class="nav-sep">|</span>
            <a @click="goTo(`/books/${currentBookId}`)">阅读</a>
            <a @click="goTo(`/books/${currentBookId}/digest`)">提炼</a>
            <a @click="goTo(`/books/${currentBookId}/chat`)">问答</a>
            <a @click="goTo(`/books/${currentBookId}/quiz`)">陪练</a>
          </template>
        </nav>
      </div>
      <div class="status-badge" :class="appStore.statusClass">
        {{ appStore.statusText }}
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  background: #f5f5f5;
  color: #333;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: #1a1a2e;
  color: white;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.app-header h1 {
  font-size: 20px;
  font-weight: 600;
  user-select: none;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-links a {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.2s;
}

.nav-links a:hover {
  color: white;
}

.nav-sep {
  color: rgba(255, 255, 255, 0.3);
  font-size: 14px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.connected {
  background: #4caf50;
  color: white;
}

.status-badge.connecting {
  background: #ff9800;
  color: white;
}

.status-badge.disconnected {
  background: #f44336;
  color: white;
}

.app-main {
  flex: 1;
  padding: 24px;
}
</style>
