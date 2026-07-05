<!--
  LLM 配置页面

  用户在此配置 AI 模型参数（Provider、API Key、模型等）。
  配置存储在 SQLite 中，重启应用后保留。
-->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getLlmSettings, saveLlmSettings } from "../api/settings";
import type { LlmSettings } from "../api/settings";

const settings = ref<LlmSettings>({
  llm_provider: "openai",
  llm_api_key: "",
  llm_api_base: "https://api.deepseek.com",
  llm_model: "",
  llm_max_tokens: "4096",
  llm_temperature: "0.7",
});

const saving = ref(false);
const saved = ref(false);

/** 加载已保存的配置 */
async function loadSettings() {
  try {
    const data = await getLlmSettings();
    settings.value = data;
  } catch {
    // 使用默认值
  }
}

/** 保存配置 */
async function handleSave() {
  saving.value = true;
  saved.value = false;
  try {
    await saveLlmSettings(settings.value);
    saved.value = true;
    setTimeout(() => (saved.value = false), 2000);
  } catch {
    alert("保存失败");
  } finally {
    saving.value = false;
  }
}

onMounted(loadSettings);
</script>

<template>
  <div class="settings-page">
    <div class="settings-card">
      <h2>AI 模型配置</h2>
      <p class="desc">配置 AI 引擎的模型参数，保存后即生效。</p>

      <!-- Provider 类型 -->
      <div class="field">
        <label>模型提供商</label>
        <select v-model="settings.llm_provider">
          <option value="openai">OpenAI 兼容（DeepSeek / 通义千问 等）</option>
          <option value="claude">Claude</option>
          <option value="ollama">Ollama（本地）</option>
        </select>
      </div>

      <!-- API Key -->
      <div class="field">
        <label>API 密钥</label>
        <input
          v-model="settings.llm_api_key"
          type="password"
          placeholder="sk-..."
        />
      </div>

      <!-- API 地址 -->
      <div class="field">
        <label>API 地址</label>
        <input v-model="settings.llm_api_base" type="text" />
      </div>

      <!-- 模型名称 -->
      <div class="field">
        <label>模型名称</label>
        <input v-model="settings.llm_model" type="text" />
      </div>

      <!-- 最大 Token -->
      <div class="field-row">
        <div class="field">
          <label>最大 Token</label>
          <input v-model="settings.llm_max_tokens" type="number" />
        </div>
        <div class="field">
          <label>温度 (0-1)</label>
          <input
            v-model="settings.llm_temperature"
            type="number"
            step="0.1"
            min="0"
            max="1"
          />
        </div>
      </div>

      <!-- 保存按钮 -->
      <div class="actions">
        <button class="btn-save" :disabled="saving" @click="handleSave">
          {{ saving ? "保存中..." : "保存配置" }}
        </button>
        <span v-if="saved" class="saved-hint">✅ 已保存</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 600px;
  margin: 0 auto;
}

.settings-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.settings-card h2 {
  font-size: 20px;
  color: #1a1a2e;
  margin-bottom: 6px;
}

.desc {
  font-size: 13px;
  color: #999;
  margin-bottom: 24px;
}

.field {
  margin-bottom: 16px;
}

.field label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
  font-weight: 500;
}

.field input,
.field select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.field input:focus,
.field select:focus {
  border-color: #1a1a2e;
}

.field-row {
  display: flex;
  gap: 12px;
}

.field-row .field {
  flex: 1;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.btn-save {
  padding: 10px 32px;
  background: #1a1a2e;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.saved-hint {
  font-size: 14px;
  color: #4caf50;
}
</style>
