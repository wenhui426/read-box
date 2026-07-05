# Read-Box 📚

> 本地多 Agent 桌面读书辅助系统 — 读书、提炼、问答与陪练，一箱搞定。

Read-Box 是一款开源的桌面应用，帮助你高效读书。它集成了多个 AI Agent，自动完成书籍解析、内容提炼、知识问答和陪练出题，让阅读从单向输入变成双向交互。

---

## 功能概览

| 功能 | 说明 |
|---|---|
| **📖 书籍解析** | 支持 PDF、EPUB、TXT 格式，自动识别章节结构 |
| **🧠 AI 提炼** | 自动生成章节摘要、关键概念、金句摘录 |
| **💬 智能问答** | 基于整本书提问，AI 回答并标注来源 |
| **📝 陪练出题** | 章节测验、全书考试、自适应出题评判 |
| **📄 笔记导出** | 一键导出 Markdown 格式的完整读书笔记 |

## 技术栈

| 层 | 技术 |
|---|---|
| **桌面壳** | Tauri 2.x (Rust) |
| **前端** | Vue 3 + TypeScript + Pinia |
| **后端** | FastAPI + Uvicorn (Python) |
| **存储** | SQLite（本地轻量） |
| **AI 引擎** | 可配置（OpenAI 兼容 / Claude / Ollama 等） |

## 项目结构

```
read-box/
├── code/               # 全部源码
│   ├── src-tauri/      # Tauri 桌面壳（Rust）
│   ├── frontend/       # Vue 3 前端
│   └── backend/        # FastAPI 后端（Python）
└── README.md
```

## 环境要求

- **Python** 3.14+
- **Node.js** 22+
- **uv**（[安装指引](https://docs.astral.sh/uv/)）
- **pnpm**（`npm install -g pnpm`）

## 快速开始（浏览器模式）

无需安装 Rust，直接在浏览器中运行。

### 1. 安装后端依赖

```bash
cd code/backend
uv sync
```

### 2. 配置环境变量

```bash
cp code/backend/.env.example code/backend/.env
```

然后编辑 `.env` 文件，填入你的 LLM API Key。
也可以通过启动后的页面「模型配置」填写，效果相同。

### 3. 安装前端依赖

```bash
cd code/frontend
pnpm install
```

### 4. 启动后端

```bash
cd code/backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8765
```

### 5. 启动前端

新开一个终端：

```bash
cd code/frontend
pnpm dev
```

### 6. 打开浏览器

访问 **http://localhost:5173** 即可使用。

## 桌面应用（Tauri）

如果需要打包为桌面应用，需额外安装 Rust 工具链。

```bash
# 安装 Rust: https://www.rust-lang.org/tools/install

# 安装 Tauri CLI
cd code
pnpm install

# 启动桌面应用
pnpm dev

# 构建安装包
pnpm build
```

构建产物在 `code/src-tauri/target/release/bundle/` 目录下。

## 配置 AI 模型

Read-Box 支持多种 AI 模型后端：

| 提供商 | API 地址 |
|---|---|
| **DeepSeek**（推荐） | `https://api.deepseek.com` |
| **OpenAI 兼容** | `https://api.openai.com/v1` |
| **Ollama（本地）** | `http://localhost:11434/v1` |

配置方式：
1. 复制 `.env.example` 为 `.env` 后编辑
2. 或启动后在页面右上角「模型配置」中填写

## 许可证

本项目采用 MIT 许可证。
