"""
AI 提炼 Agent

基于已解析的书籍章节内容，调用 LLM 生成摘要、关键概念和金句摘录。
支持全书提炼和单章提炼，结果存入 SQLite。
"""

import json
from datetime import datetime
from typing import Optional

from app.agents.base import BaseAgent
from app.agents.prompts import (
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_PROMPT,
    CONCEPTS_SYSTEM_PROMPT,
    CONCEPTS_USER_PROMPT,
    QUOTES_SYSTEM_PROMPT,
    QUOTES_USER_PROMPT,
    EXPORT_TEMPLATE,
    CHAPTER_TOC_TEMPLATE,
    CHAPTER_CONTENT_TEMPLATE,
)
from app.database import get_db


# 最大重试次数
MAX_RETRIES = 2


class DigestAgent(BaseAgent):
    """书籍提炼 Agent"""

    async def run(self, **kwargs) -> dict:
        """
        执行提炼任务（可扩展接口，后续统一使用）

        Args:
            **kwargs: 需包含 book_id

        Returns:
            包含 digest_id 的结果字典
        """
        book_id = kwargs.get("book_id")
        chapter_id = kwargs.get("chapter_id")
        if chapter_id:
            return await self.digest_single_chapter(book_id, chapter_id)
        return await self.digest_book(book_id)

    async def digest_book(self, book_id: int) -> dict:
        """
        提炼全书：逐章处理，串行调用 LLM

        Args:
            book_id: 书籍 ID

        Returns:
            包含 digest_id 和状态的结果
        """
        # 创建提炼任务记录
        db = await get_db()

        # 获取总章节数
        rows = await db.execute_fetchall(
            "SELECT COUNT(*) FROM chapters WHERE book_id = ?", (book_id,)
        )
        total_chapters = rows[0][0] if rows else 0

        # 创建 digest 记录
        cursor = await db.execute(
            """
            INSERT INTO digests (book_id, status, total_chapters, processed_chapters)
            VALUES (?, 'processing', ?, 0)
            """,
            (book_id, total_chapters),
        )
        digest_id = cursor.lastrowid
        await db.commit()

        # 获取所有章节
        chapters = await db.execute_fetchall(
            "SELECT id, title, content FROM chapters WHERE book_id = ? ORDER BY sort_order",
            (book_id,),
        )

        processed = 0
        for chapter_row in chapters:
            ch_id, ch_title, ch_content = chapter_row
            success = await self._process_chapter(digest_id, ch_id, ch_title, ch_content)
            if success:
                processed += 1

            # 更新进度
            await db.execute(
                "UPDATE digests SET processed_chapters = ? WHERE id = ?",
                (processed, digest_id),
            )
            await db.commit()

        # 更新完成状态
        status = "completed" if processed == total_chapters else ("partial" if processed > 0 else "failed")
        await db.execute(
            "UPDATE digests SET status = ?, processed_chapters = ? WHERE id = ?",
            (status, processed, digest_id),
        )
        await db.commit()
        await db.close()

        return {"digest_id": digest_id, "status": status, "processed": processed, "total": total_chapters}

    async def digest_single_chapter(self, book_id: int, chapter_id: int) -> dict:
        """
        提炼单章

        Args:
            book_id: 书籍 ID
            chapter_id: 章节 ID

        Returns:
            处理结果
        """
        db = await get_db()

        # 获取章节内容
        rows = await db.execute_fetchall(
            "SELECT title, content FROM chapters WHERE id = ? AND book_id = ?",
            (chapter_id, book_id),
        )
        if not rows:
            await db.close()
            return {"status": "failed", "error": "章节不存在"}

        ch_title, ch_content = rows[0]

        # 查找或创建 digest 记录
        digest_rows = await db.execute_fetchall(
            "SELECT id FROM digests WHERE book_id = ? AND status = 'processing'",
            (book_id,),
        )
        if digest_rows:
            digest_id = digest_rows[0][0]
        else:
            cursor = await db.execute(
                "INSERT INTO digests (book_id, status, total_chapters, processed_chapters) VALUES (?, 'processing', 0, 0)",
                (book_id,),
            )
            digest_id = cursor.lastrowid
            await db.commit()

        success = await self._process_chapter(digest_id, chapter_id, ch_title, ch_content)
        await db.close()

        return {"status": "completed" if success else "failed", "chapter_id": chapter_id}

    async def _process_chapter(
        self, digest_id: int, chapter_id: int, title: str, content: str
    ) -> bool:
        """
        处理单章：生成摘要、概念、金句

        Args:
            digest_id: 提炼任务 ID
            chapter_id: 章节 ID
            title: 章节标题
            content: 章节内容

        Returns:
            True 表示成功
        """
        # 读取该章节的用户高亮，拼入内容（高亮内容获得更高权重）
        highlights_text = ""
        try:
            hl_db = await get_db()
            hl_rows = await hl_db.execute_fetchall(
                "SELECT text, note FROM highlights WHERE chapter_id = ? ORDER BY created_at",
                (chapter_id,),
            )
            if hl_rows:
                hl_parts = []
                for hl_row in hl_rows:
                    hl_text = hl_row[0]
                    hl_note = hl_row[1]
                    if hl_note:
                        hl_parts.append(f"📍 {hl_text}（批注：{hl_note}）")
                    else:
                        hl_parts.append(f"📍 {hl_text}")
                highlights_text = "\n".join(hl_parts)
            await hl_db.close()
        except Exception:
            pass

        # 组装内容：高亮部分在前，权重更高
        enhanced_content = content
        if highlights_text:
            enhanced_content = (
                "【用户标注的高优先级内容】\n"
                f"{highlights_text}\n\n"
                "【完整章节内容】\n"
                f"{content}"
            )

        # 限制内容长度（防止超出 LLM 上下文）
        max_content_len = 8000
        truncated_content = enhanced_content[:max_content_len]
        if len(enhanced_content) > max_content_len:
            truncated_content += "\n\n[内容过长，已截断]"

        # 生成摘要
        summary = await self._generate_summary(title, truncated_content)

        # 提取关键概念
        concepts = await self._extract_concepts(title, truncated_content)

        # 提取金句
        quotes = await self._extract_quotes(title, truncated_content)

        # 写入数据库
        try:
            db = await get_db()
            cursor = await db.execute(
                """
                INSERT INTO chapter_digests (digest_id, chapter_id, summary, status)
                VALUES (?, ?, ?, 'completed')
                """,
                (digest_id, chapter_id, summary or "摘要生成失败"),
            )
            cd_id = cursor.lastrowid  # 获取自增 ID
            await db.commit()

            # 写入概念
            for idx, concept in enumerate(concepts):
                await db.execute(
                    "INSERT INTO key_concepts (chapter_digest_id, term, explanation, sort_order) VALUES (?, ?, ?, ?)",
                    (cd_id, concept.get("term", ""), concept.get("explanation", ""), idx),
                )

            # 写入金句
            for idx, quote in enumerate(quotes):
                await db.execute(
                    "INSERT INTO golden_quotes (chapter_digest_id, quote, reason, sort_order) VALUES (?, ?, ?, ?)",
                    (cd_id, quote.get("quote", ""), quote.get("reason", ""), idx),
                )

            await db.commit()
            await db.close()
            return True
        except Exception as e:
            try:
                await db.close()
            except Exception:
                pass
            print(f"章节处理失败: {e}")
            return False

    async def _call_llm(self, system: str, user: str) -> Optional[str]:
        """
        调用 LLM 并处理重试

        Args:
            system: 系统 prompt
            user: 用户 prompt

        Returns:
            LLM 响应文本，失败返回 None
        """
        for attempt in range(MAX_RETRIES + 1):
            try:
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
                return await self.provider.chat(messages)
            except Exception as e:
                if attempt < MAX_RETRIES:
                    continue
                return None

    async def _generate_summary(self, title: str, content: str) -> str:
        """生成章节摘要"""
        user_prompt = SUMMARY_USER_PROMPT.format(
            chapter_title=title, chapter_content=content
        )
        result = await self._call_llm(SUMMARY_SYSTEM_PROMPT, user_prompt)
        return result or ""

    async def _extract_concepts(self, title: str, content: str) -> list[dict]:
        """提取关键概念"""
        user_prompt = CONCEPTS_USER_PROMPT.format(
            chapter_title=title, chapter_content=content
        )
        result = await self._call_llm(CONCEPTS_SYSTEM_PROMPT, user_prompt)
        if not result:
            return []
        return self._parse_json_list(result)

    async def _extract_quotes(self, title: str, content: str) -> list[dict]:
        """提取金句"""
        user_prompt = QUOTES_USER_PROMPT.format(
            chapter_title=title, chapter_content=content
        )
        result = await self._call_llm(QUOTES_SYSTEM_PROMPT, user_prompt)
        if not result:
            return []
        return self._parse_json_list(result)

    def _parse_json_list(self, text: str) -> list[dict]:
        """
        解析 LLM 返回的 JSON 列表

        Args:
            text: LLM 返回的文本

        Returns:
            解析后的字典列表
        """
        # 尝试提取 JSON 部分（LLM 有时会额外输出说明文字）
        try:
            start = text.index("[")
            end = text.rindex("]") + 1
            json_str = text[start:end]
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            return []

    async def export_markdown(self, book_id: int) -> Optional[str]:
        """
        导出全书读书笔记 Markdown

        Args:
            book_id: 书籍 ID

        Returns:
            Markdown 文本，失败返回 None
        """
        db = await get_db()

        # 获取书籍信息
        books = await db.execute_fetchall(
            "SELECT title, author FROM books WHERE id = ?", (book_id,)
        )
        if not books:
            await db.close()
            return None
        book_title, book_author = books[0]

        # 获取章节列表
        chapters = await db.execute_fetchall(
            "SELECT id, title, sort_order FROM chapters WHERE book_id = ? ORDER BY sort_order",
            (book_id,),
        )

        chapters_toc = []
        chapters_content = []
        all_concepts = []
        all_quotes = []

        for idx, (ch_id, ch_title, ch_order) in enumerate(chapters, 1):
            chapters_toc.append(CHAPTER_TOC_TEMPLATE.format(
                chapter_num=idx, chapter_title=ch_title
            ))

            # 获取该章节的提炼结果
            cds = await db.execute_fetchall(
                "SELECT id, summary FROM chapter_digests WHERE chapter_id = ? ORDER BY id DESC LIMIT 1",
                (ch_id,),
            )
            if cds:
                cd_id, summary = cds[0]

                # 获取概念
                concepts_rows = await db.execute_fetchall(
                    "SELECT term, explanation FROM key_concepts WHERE chapter_digest_id = ? ORDER BY sort_order",
                    (cd_id,),
                )
                concepts_text = "\n".join(
                    f"- **{r[0]}**：{r[1]}" for r in concepts_rows
                ) or "（暂无）"

                # 获取金句
                quotes_rows = await db.execute_fetchall(
                    "SELECT quote, reason FROM golden_quotes WHERE chapter_digest_id = ? ORDER BY sort_order",
                    (cd_id,),
                )
                quotes_text = "\n".join(
                    f'- "{r[0]}"\n  — 摘录理由：{r[1]}'
                    for r in quotes_rows
                ) or "（暂无）"

                chapters_content.append(CHAPTER_CONTENT_TEMPLATE.format(
                    chapter_num=idx,
                    chapter_title=ch_title,
                    summary=summary or "（暂无摘要）",
                    concepts=concepts_text,
                    quotes=quotes_text,
                ))

                # 汇总概念和金句
                for r in concepts_rows:
                    all_concepts.append(f"- **{r[0]}**：{r[1]}")
                for r in quotes_rows:
                    all_quotes.append(f'- "{r[0]}"')

        await db.close()

        return EXPORT_TEMPLATE.format(
            book_title=book_title,
            book_author=book_author or "未知作者",
            digest_date=datetime.now().strftime("%Y-%m-%d"),
            chapters_toc="\n".join(chapters_toc),
            chapters_content="\n".join(chapters_content),
            all_concepts="\n".join(all_concepts) or "（暂无）",
            all_quotes="\n".join(all_quotes) or "（暂无）",
        )
