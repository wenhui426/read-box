"""
问答 Agent

基于已解析的书籍内容回答用户问题。
支持多轮对话、引用标注、超出范围检测。
与陪练 Agent 共享上下文管理器。
"""

from typing import AsyncGenerator, Optional

from app.agents.base import BaseAgent
from app.agents.prompts import QA_SYSTEM_PROMPT, QA_USER_PROMPT
from app.context.manager import context_manager
from app.database import get_db


class QAAgent(BaseAgent):
    """
    问答 Agent

    根据书籍内容回答用户提问。
    自动利用提炼结果增强回答质量。
    """

    async def run(self, **kwargs) -> dict:
        """实现 BaseAgent 抽象方法，委托给 ask"""
        book_id = kwargs.get("book_id")
        question = kwargs.get("question", "")
        # ask 是生成器，这里收集完整结果返回
        result = ""
        async for chunk in self.ask(book_id, question):
            result += chunk
        return {"answer": result}

    async def ask(self, book_id: int, question: str) -> AsyncGenerator[str, None]:
        """
        提问并获取流式回答

        向 LLM 提问，以 SSE 流式格式逐字返回回答。

        Args:
            book_id: 书籍 ID
            question: 用户问题
        """
        # 设置上下文（切换书籍时自动清空历史）
        db = await get_db()

        # 获取书籍信息
        books = await db.execute_fetchall(
            "SELECT title FROM books WHERE id = ?", (book_id,)
        )
        if not books:
            yield "错误：书籍不存在"
            return

        book_title = books[0][0]
        context_manager.set_book(book_id, book_title)

        # 获取章节摘要（提炼 Agent 的输出，如有）
        summaries = await db.execute_fetchall(
            """
            SELECT cd.summary, ch.title
            FROM chapter_digests cd
            JOIN chapters ch ON cd.chapter_id = ch.id
            WHERE ch.book_id = ?
            ORDER BY ch.sort_order
            LIMIT 5
            """,
            (book_id,),
        )
        book_summary = ""
        if summaries:
            parts = []
            for summary, ch_title in summaries:
                if summary:
                    parts.append(f"《{ch_title}》：{summary[:200]}")
            book_summary = "\n".join(parts)

        # 获取前几个章节的原文作为上下文
        chapters = await db.execute_fetchall(
            "SELECT title, content FROM chapters WHERE book_id = ? ORDER BY sort_order LIMIT 3",
            (book_id,),
        )
        chapter_content = ""
        if chapters:
            parts = []
            for ch_title, content in chapters:
                parts.append(f"【{ch_title}】\n{content[:1000]}")
            chapter_content = "\n\n".join(parts)

        await db.close()

        # 获取对话历史
        history = context_manager.get_history()

        # 1. 最近 12 条对话（最近 6 轮问答）
        recent = history[-12:] if len(history) >= 12 else history
        chat_history = "\n".join(
            f"{'用户' if m['role'] == 'user' else '助手'}：{m['content'][:300]}"
            for m in recent
        )

        # 2. 如果用户提到了之前的某个内容，从全部历史中检索相关段落
        # 关键词触发：之前、前面、刚才、上文、那个概念、你说过等
        reference_keywords = ["之前", "前面", "刚才", "上文", "你说过", "你刚才", "之前说的", "那个"]
        extra_context = ""
        if any(kw in question for kw in reference_keywords):
            # 提取问题中的关键词（去掉常见停用词）
            import re
            words = set(re.findall(r'[一-鿿\w]{2,}', question))
            # 过滤掉引用关键词本身和常见词
            skip_words = {"之前", "前面", "刚才", "上文", "那个", "什么", "哪里", "怎么", "为什么", "能否"}
            keywords = words - skip_words

            # 在全部历史中搜索包含这些关键词的消息
            if keywords:
                matched = []
                for msg in history:
                    for kw in keywords:
                        if kw in msg["content"]:
                            role_label = "用户" if msg["role"] == "user" else "助手"
                            # 截取包含关键词的上下文
                            idx = msg["content"].find(kw)
                            start = max(0, idx - 30)
                            end = min(len(msg["content"]), idx + len(kw) + 100)
                            snippet = msg["content"][start:end]
                            matched.append(f"[{role_label}相关] ...{snippet}...")
                            break

                if matched:
                    extra_context = "\n--- 以下是与当前问题相关的历史记录 ---\n" + "\n".join(matched[-3:])

        chat_history = (chat_history or "（无历史对话）") + extra_context

        # 构建 prompt
        user_prompt = QA_USER_PROMPT.format(
            book_title=book_title,
            book_summary=book_summary or "（暂无提炼结果）",
            chapter_content=chapter_content or "（暂无章节内容）",
            chat_history=chat_history,
            question=question,
        )

        # 记录用户消息（内存 + 数据库持久化）
        context_manager.add_message("user", question)
        try:
            await db.execute(
                "INSERT INTO chat_history (book_id, role, content) VALUES (?, 'user', ?)",
                (book_id, question),
            )
        except Exception:
            pass  # 数据库写入失败不影响功能
        messages = [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        full_response = ""
        try:
            # 当前 Provider 暂不支持流式，先模拟逐字返回
            response = await self.provider.chat(messages)
            full_response = response

            # 模拟流式输出（每次 5-10 个字）
            import asyncio
            chunk_size = 5
            for i in range(0, len(response), chunk_size):
                yield response[i : i + chunk_size]
                await asyncio.sleep(0.02)

        except Exception as e:
            error_msg = f"\n\n调用 AI 失败：{str(e)}"
            yield error_msg
            full_response += error_msg

        # 记录助手回复（内存 + 数据库持久化）
        context_manager.add_message("assistant", full_response)
        try:
            await db.execute(
                "INSERT INTO chat_history (book_id, role, content) VALUES (?, 'assistant', ?)",
                (book_id, full_response),
            )
            await db.commit()
        except Exception:
            pass
        await db.close()

    async def clear_context(self, book_id: int) -> None:
        """
        清空指定书籍的对话上下文

        Args:
            book_id: 书籍 ID
        """
        if context_manager.current_book_id == book_id:
            context_manager.clear()
