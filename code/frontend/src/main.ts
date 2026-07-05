/**
 * Read-Box 前端应用入口
 *
 * 初始化 Vue 3 应用实例，挂载路由（Pinia 状态管理）和根组件。
 */
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";

// 创建 Vue 应用实例
const app = createApp(App);

// 注册 Pinia 状态管理
app.use(createPinia());

// 注册 Vue Router
app.use(router);

// 挂载到 index.html 中的 #app 元素
app.mount("#app");
