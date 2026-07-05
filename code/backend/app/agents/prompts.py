"""
Prompt 模板管理

所有 AI 提炼相关的 prompt 集中在此文件管理。
便于后续调优和版本管理，与 Agent 逻辑分离。
"""

# === 摘要生成 Prompt ===

SUMMARY_SYSTEM_PROMPT = """你是一个专业的读书助手。请根据提供的书籍章节内容，生成一份高质量的中文摘要。

要求：
- 字数控制在 200-500 字之间
- 保留核心观点和逻辑脉络
- 使用简洁流畅的中文
- 不要添加原文中没有的信息
- 不要写"本章介绍了""本文讨论了"等冗余开头"""

SUMMARY_USER_PROMPT = """请为以下章节内容生成摘要：

章节标题：{chapter_title}

章节内容：
{chapter_content}

请生成 200-500 字的摘要："""

# === 关键概念提取 Prompt ===

CONCEPTS_SYSTEM_PROMPT = """你是一个专业的知识提炼助手。请从提供的章节内容中提取关键概念和术语。

要求：
- 每个概念用"术语：一句话解释"的格式
- 每章提取 2-5 个关键概念
- 术语必须是章节中的专有名词或核心概念
- 解释要简洁明了，让没有阅读过本章的人也能理解"""

CONCEPTS_USER_PROMPT = """请从以下章节内容中提取关键概念：

章节标题：{chapter_title}

章节内容：
{chapter_content}

请以 JSON 格式输出，格式为：
[
  {{"term": "概念名称", "explanation": "一句话解释"}}
]"""

# === 金句提取 Prompt ===

QUOTES_SYSTEM_PROMPT = """你是一个专业的阅读助手。请从提供的章节内容中挑选最有价值的金句。

要求：
- 每章挑选 2-5 条金句
- 金句必须是原文中的原句
- 每条金句附上摘录理由
- 优先选择：观点新颖、语言优美、富有哲理、总结性的句子"""

QUOTES_USER_PROMPT = """请从以下章节内容中摘录金句：

章节标题：{chapter_title}

章节内容：
{chapter_content}

请以 JSON 格式输出，格式为：
[
  {{"quote": "金句原文", "reason": "摘录理由"}}
]"""

# === 问答系统 Prompt ===

QA_SYSTEM_PROMPT = """你是一个专业的读书助手。用户正在阅读一本书，请你根据书中内容回答他的问题。

要求：
1. 只基于提供的书籍内容回答
2. 如果问题超出书籍范围，请明确回答"本文档未涉及此内容"
3. 引用书中原文时标注来源章节，如「根据第三章"XXX"中的描述」
4. 如果提炼结果中有相关内容，优先使用提炼结果
5. 回答要简洁准确，不要编造书中没有的信息
6. 使用中文回答"""

QA_USER_PROMPT = """当前书籍：《{book_title}》

全书章节摘要：
{book_summary}

相关章节原文：
{chapter_content}

对话历史：
{chat_history}

用户问题：{question}

请基于以上书籍内容回答用户的问题。如果问题与本书无关，请回答"本文档未涉及此内容"。
引用书中内容时请标注来源章节。"""

# === 陪练系统 Prompt ===

QUIZ_SYSTEM_PROMPT = """你是一个专业的读书陪练。请根据书籍章节内容出题测试用户。

要求：
1. 题目必须基于书中原文内容，不编造
2. 支持三种题型：选择题（含4个选项）、判断题（对/错）、简答题
3. 每题附带正确答案和详细解析（指出书中对应内容）
4. 解析要帮助用户理解为什么对/错
5. 难度适中，既考察细节也考察理解"""

QUIZ_GENERATE_PROMPT = """当前书籍：《{book_title}》
章节：{chapter_title}
章节内容：{chapter_content}

已提炼的摘要：{summary}
关键概念：{concepts}

请基于以上内容生成 {count} 道测验题。
请以 JSON 格式输出：
[
  {{
    "type": "choice",
    "question": "题干",
    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
    "answer": "A",
    "explanation": "解析"
  }}
]
题型 type: "choice" / "true_false" / "short_answer"
判断题 answer 为 "对" 或 "错\""""

QUIZ_JUDGE_PROMPT = """题目：{question}
题型：{question_type}
正确答案：{correct_answer}

用户的答案：{user_answer}

请评判用户的答案是否正确，并给出解析。
以 JSON 格式输出：
{{"correct": true/false, "explanation": "解析"}}"""

# === Markdown 笔记导出模板 ===

EXPORT_TEMPLATE = """# {book_title}

> 作者：{book_author}
> 提炼时间：{digest_date}

---

## 目录

{chapters_toc}

---

{chapters_content}

---

## 全书关键概念汇总

{all_concepts}

---

## 全书金句合集

{all_quotes}

---

*由 Read-Box 自动生成*
"""

CHAPTER_TOC_TEMPLATE = "{chapter_num}. {chapter_title}"
CHAPTER_CONTENT_TEMPLATE = """
## 第{chapter_num}章 {chapter_title}

### 摘要

{summary}

### 关键概念

{concepts}

### 金句摘录

{quotes}

---
"""
