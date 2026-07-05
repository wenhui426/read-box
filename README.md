<!-- Language toggle / 语言切换 -->
<div align="center">

# Read-Box 📚

[🇺🇸 English](#english) · [🇨🇳 中文](#chinese)

</div>

---

<details open>
<summary><strong>🇺🇸 English</strong></summary>

<br>

> Local multi-agent desktop reading assistant — book parsing, AI digest, Q&A, and quiz, all in one box.

Read-Box is an open-source desktop application that helps you read more efficiently. It integrates multiple AI Agents to automatically parse books, generate digests, answer questions, and create practice quizzes — turning reading from a one-way input into interactive learning.

📥 **Download**: Get the Windows installer from [Releases](https://github.com/wenhui426/read-box/releases) (double-click to install, no dependencies required).

---

## Features

| Feature | Description |
|---|---|
| **📖 Book Parser** | PDF, EPUB, TXT — auto-detect chapter structure |
| **🧠 AI Digest** | Chapter summaries, key concepts, golden quotes |
| **💬 AI Q&A** | Ask questions based on book content with source citations |
| **📝 Quiz** | Chapter quizzes, full-book exams, adaptive testing |
| **📄 Export** | Export full reading notes as Markdown |

## Project Structure

```
read-box/
├── code/               # Desktop app source code
│   ├── src-tauri/      # Tauri desktop shell (Rust)
│   ├── frontend/       # Vue 3 frontend
│   └── backend/        # FastAPI backend (Python)
├── skills/
│   └── read-box/       # AI Skill for coding assistants
└── README.md
```

## Quick Start

| Method | Who | Description |
|---|---|---|
| **🖥️ Desktop Installer** | End users | Download exe, install and use — zero config |
| **🌐 Browser Mode** | Developers | Start backend + frontend, open browser |
| **🤖 AI Skill** | Claude Code / Codex users | Install skill, use in conversation |

### 🖥️ Desktop Installer

Download `Read-Box_x.x.x_x64-setup.exe` from [Releases](https://github.com/wenhui426/read-box/releases) and run it.

**No Python, Node.js, or any dependencies required.**

### 🌐 Browser Mode

**Prerequisites**: Python 3.14+, Node.js 22+, [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/)

```bash
# 1. Install backend dependencies
cd code/backend
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env with your LLM API Key

# 3. Install frontend dependencies
cd ../frontend
pnpm install

# 4. Start backend (terminal 1)
cd ../backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8765

# 5. Start frontend (terminal 2)
cd ../frontend
pnpm dev

# 6. Open http://localhost:5173
```

### 🤖 AI Skill（Claude Code / Codex / Cursor）

Use Read-Box's reading capabilities directly in your AI coding assistant.

**Install (Claude Code):**

```bash
mkdir -p ~/.claude/skills/read-box
cp -r skills/read-box/* ~/.claude/skills/read-box/
```

**Usage:**

| Action | Say |
|---|---|
| **Import book** | `/read-book C:\books\three-body.pdf` |
| **Digest** | "Summarize this book" |
| **Q&A** | "What is the main idea?" |
| **Quiz** | "Quiz me on chapter 3" |
| **Export** | "Export as Markdown" |

Outputs are saved to `./read-box-output/{book-name}/`.

### Build Desktop App

```bash
# Install Rust: https://www.rust-lang.org/tools/install
cd code
pnpm install
pnpm tauri build
```

Output: `code/src-tauri/target/release/bundle/nsis/`

## LLM Configuration

| Provider | API Base URL |
|---|---|
| **DeepSeek** | `https://api.deepseek.com` |
| **OpenAI-compatible** | `https://api.openai.com/v1` |
| **Ollama (local)** | `http://localhost:11434/v1` |

Configure via the Settings page in the app, or via `.env` file.

## License

MIT

</details>

---

<details>
<summary><strong>🇨🇳 中文</strong></summary>

<br>

# Read-Box 📚

> 本地多 Agent 桌面读书辅助系统 — 读书、提炼、问答与陪练，一箱搞定。

Read-Box 是一款开源的桌面应用，帮助你高效读书。它集成了多个 AI Agent，自动完成书籍解析、内容提炼、知识问答和陪练出题，让阅读从单向输入变成双向交互。

📥 **下载桌面版**：前往 [Releases](https://github.com/wenhui426/read-box/releases) 下载安装包（Windows，双击即用）

---

## 功能概览

| 功能 | 说明 |
|---|---|
| **📖 书籍解析** | 支持 PDF、EPUB、TXT 格式，自动识别章节结构 |
| **🧠 AI 提炼** | 自动生成章节摘要、关键概念、金句摘录 |
| **💬 智能问答** | 基于整本书提问，AI 回答并标注来源 |
| **📝 陪练出题** | 章节测验、全书考试、自适应出题评判 |
| **📄 笔记导出** | 一键导出 Markdown 格式的完整读书笔记 |

## 项目结构

```
read-box/
├── code/               # 桌面应用源码
│   ├── src-tauri/      # Tauri 桌面壳（Rust）
│   ├── frontend/       # Vue 3 前端
│   └── backend/        # FastAPI 后端（Python）
├── skills/
│   └── read-box/       # AI 读书 Skill
└── README.md
```

## 使用方式

| 方式 | 适合人群 | 说明 |
|---|---|---|
| **🖥️ 桌面安装包** | 普通用户 | 下载 exe 安装即用，无需任何配置环境 |
| **🌐 浏览器模式** | 开发者 | 启动前后端服务，浏览器访问 |
| **🤖 AI Skill** | Claude Code / Codex 等用户 | 安装 Skill，对话中直接使用 |

---

## 🖥️ 桌面安装包

从 [Releases](https://github.com/wenhui426/read-box/releases) 下载 `Read-Box_x.x.x_x64-setup.exe`，双击安装即可使用。

**包含完整运行环境，无需安装 Python / Node.js 等任何依赖。**

## 🌐 浏览器模式

无需安装 Rust，开发环境下直接在浏览器中运行。

### 环境要求

- **Python** 3.14+、**Node.js** 22+
- **uv**（[安装指引](https://docs.astral.sh/uv/)）、**pnpm**（`npm install -g pnpm`）

### 快速启动

```bash
# 1. 安装后端依赖
cd code/backend
uv sync

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key

# 3. 安装前端依赖
cd ../frontend
pnpm install

# 4. 启动后端（终端1）
cd ../backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8765

# 5. 启动前端（终端2）
cd ../frontend
pnpm dev

# 6. 浏览器访问 http://localhost:5173
```

## 🤖 AI Skill（Claude Code / Codex / Cursor 等）

在 AI 编码工具中直接使用 Read-Box 的读书能力，无需启动任何服务。

### 安装（Claude Code 为例）

```bash
mkdir -p ~/.claude/skills/read-box
cp -r skills/read-box/* ~/.claude/skills/read-box/
```

### 使用

唯一入口命令是 `/read-book`，导入后直接用自然语言交互：

| 操作 | 怎么说 |
|---|---|
| **导入书籍** | `/read-book C:\books\三体.pdf` |
| **提炼全书** | "帮我提炼这本书" 或 "生成每章摘要" |
| **问答** | 直接提问，如"这本书的核心观点是什么？" |
| **陪练出题** | "考考我" 或 "出5道题" |
| **导出笔记** | "导出笔记" 或 "生成 Markdown" |

### 文件输出

生成的笔记存放在当前目录下的 `read-box-output/{书名}/` 中。

## 配置 AI 模型

| 提供商 | API 地址 |
|---|---|
| **DeepSeek**（推荐） | `https://api.deepseek.com` |
| **OpenAI 兼容** | `https://api.openai.com/v1` |
| **Ollama（本地）** | `http://localhost:11434/v1` |

配置方式：
- **桌面版/浏览器模式**：启动后在页面顶部「模型配置」中填写
- **AI Skill 模式**：直接使用 AI 自身能力，无需额外配置

## 桌面版构建

如需自行打包桌面应用：

```bash
# 安装 Rust: https://www.rust-lang.org/tools/install
cd code
pnpm install
pnpm tauri build
```

构建产物在 `code/src-tauri/target/release/bundle/nsis/` 目录下。

## 许可证

本项目采用 MIT 许可证。

</details>
