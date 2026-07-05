<div align="center">

# Read-Box 📚

> Local multi-agent desktop reading assistant — book parsing, AI digest, Q&A, and quiz, all in one box.

[🇨🇳 中文版](README.zh-CN.md)

</div>

---

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
