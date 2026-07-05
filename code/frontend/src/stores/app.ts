/**
 * 全局应用状态管理
 *
 * 使用 Pinia 管理应用级别的状态：后端连接状态、版本信息等。
 * 采用组合式 API（setup store）模式。
 */
import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { checkHealth } from "../api/client";

/** 后端连接状态枚举 */
export type BackendStatus = "connecting" | "connected" | "disconnected";

export const useAppStore = defineStore("app", () => {
  // --- 状态 ---

  /** 后端服务连接状态，默认为连接中 */
  const backendStatus = ref<BackendStatus>("connecting");

  /** 后端版本号（从健康检查接口获取） */
  const backendVersion = ref("");

  // --- 计算属性（根据 backendStatus 动态计算）---

  /** 状态徽章的 CSS 类名，随连接状态变化 */
  const statusClass = computed(() => {
    switch (backendStatus.value) {
      case "connected":
        return "connected";
      case "connecting":
        return "connecting";
      case "disconnected":
        return "disconnected";
    }
  });

  /** 状态徽章显示的文字，随连接状态变化 */
  const statusText = computed(() => {
    switch (backendStatus.value) {
      case "connected":
        return "已连接";
      case "connecting":
        return "连接中...";
      case "disconnected":
        return "连接失败";
    }
  });

  // --- 方法 ---

  /**
   * 检查后端服务状态
   *
   * 页面加载时自动调用。由于后端的启动可能比前端慢（Tauri 需要先启动 Python 进程），
   * 这里采用轮询策略：每 500ms 检查一次，最多 20 次（约 10 秒）。
   */
  async function checkBackendStatus(): Promise<void> {
    backendStatus.value = "connecting";
    for (let i = 0; i < 20; i++) {
      try {
        const health = await checkHealth();
        if (health.status === "ok") {
          backendStatus.value = "connected";
          backendVersion.value = health.version;
          return;
        }
      } catch {
        // 后端尚未就绪，静默重试
      }
      // 等待 500ms 后再次尝试
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    // 所有重试均失败
    backendStatus.value = "disconnected";
  }

  // 暴露状态、计算属性和方法供组件使用
  return {
    backendStatus,
    backendVersion,
    statusClass,
    statusText,
    checkBackendStatus,
  };
});
