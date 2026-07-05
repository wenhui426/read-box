"""
陪练 Agent

基于书籍章节内容自动生成测验题目，评判用户答案。
支持章节测验、全书考试、自适应陪练三种模式。
与问答 Agent 共享 ContextManager。
"""

import json
import random
from typing import Optional

from app.agents.base import BaseAgent
from app.agents.prompts import QUIZ_SYSTEM_PROMPT, QUIZ_GENERATE_PROMPT, QUIZ_JUDGE_PROMPT
from app.context.manager import context_manager
from app.database import get_db


class QuizAgent(BaseAgent):
    """
    陪练 Agent

    支持三种模式：
    - 章节测验：基于单章内容出题
    - 全书考试：综合全书内容出题
    - 自适应陪练：连续出题 + 实时评判
    """

    async def start_exam(self, book_id: int, count: int = 10) -> list[dict]:
        """
        全书考试：综合全书内容出题

        读取所有章节的摘要或原文，合并后调用 LLM 生成跨章节考题。

        Args:
            book_id: 书籍 ID
            count: 题目数量

        Returns:
            题目列表
        """
        from app.database import get_db
        db = await get_db()

        # 获取提炼摘要（优先）或章节原文
        summaries = await db.execute_fetchall(
            """
            SELECT cd.summary, ch.title
            FROM chapter_digests cd
            JOIN chapters ch ON cd.chapter_id = ch.id
            WHERE ch.book_id = ?
            ORDER BY ch.sort_order
            """,
            (book_id,),
        )

        merged_content = ""
        if summaries:
            parts = []
            for summary, title in summaries:
                if summary and len(summary) > 10:
                    parts.append(f"【{title}】\n{summary[:500]}")
            merged_content = "\n\n".join(parts)

        # 如果没有提炼结果，直接读取章节原文
        if not merged_content:
            chapters = await db.execute_fetchall(
                "SELECT title, content FROM chapters WHERE book_id = ? ORDER BY sort_order LIMIT 5",
                (book_id,),
            )
            parts = []
            for title, content in chapters:
                parts.append(f"【{title}】\n{content[:1000]}")
            merged_content = "\n\n".join(parts)

        await db.close()

        prompt = QUIZ_GENERATE_PROMPT.format(
            book_title=context_manager.current_book_title or "未知",
            chapter_title="全书综合",
            chapter_content=merged_content[:5000],
            summary="",
            concepts="",
            count=count,
        )

        messages = [
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = await self.provider.chat(messages)
        questions = self._parse_questions(response)

        context_manager.set_book(book_id)
        context_manager.set_quiz_progress({
            "mode": "exam",
            "questions": questions,
            "current_index": 0,
            "correct_count": 0,
            "total_count": len(questions),
        })

        return questions

    async def run(self, **kwargs) -> dict:
        """实现 BaseAgent 抽象方法"""
        return {"status": "ok"}

    async def start_chapter_quiz(self, book_id: int, chapter_id: int, count: int = 5) -> list[dict]:
        """
        启动章节测验

        基于指定章节内容生成测验题。

        Args:
            book_id: 书籍 ID
            chapter_id: 章节 ID
            count: 题目数量

        Returns:
            题目列表
        """
        db = await get_db()
        # 获取章节内容 + 提炼结果
        chapters = await db.execute_fetchall(
            "SELECT title, content FROM chapters WHERE id = ? AND book_id = ?",
            (chapter_id, book_id),
        )
        if not chapters:
            await db.close()
            return []

        ch_title, ch_content = chapters[0]
        summary = ""
        concepts = ""

        # 获取提炼结果
        cds = await db.execute_fetchall(
            "SELECT summary FROM chapter_digests WHERE chapter_id = ? ORDER BY id DESC LIMIT 1",
            (chapter_id,),
        )
        if cds:
            summary = cds[0][0][:500] if cds[0][0] else ""

        concept_rows = await db.execute_fetchall(
            "SELECT term, explanation FROM key_concepts WHERE chapter_digest_id = (SELECT id FROM chapter_digests WHERE chapter_id = ? ORDER BY id DESC LIMIT 1)",
            (chapter_id,),
        )
        if concept_rows:
            concepts = "; ".join(f"{r[0]}: {r[1]}" for r in concept_rows)

        await db.close()

        prompt = QUIZ_GENERATE_PROMPT.format(
            book_title=context_manager.current_book_title or "未知",
            chapter_title=ch_title,
            chapter_content=ch_content[:3000],
            summary=summary or "（暂无）",
            concepts=concepts or "（暂无）",
            count=count,
        )

        messages = [
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = await self.provider.chat(messages)
        questions = self._parse_questions(response)

        # 保存会话状态
        context_manager.set_book(book_id)
        context_manager.set_chapter(chapter_id)
        context_manager.set_quiz_progress({
            "mode": "chapter",
            "questions": questions,
            "current_index": 0,
            "correct_count": 0,
            "total_count": len(questions),
        })

        return questions

    async def judge_answer(self, question: dict, user_answer: str) -> dict:
        """
        评判用户答案

        Args:
            question: 题目字典
            user_answer: 用户答案

        Returns:
            评判结果 {correct, explanation}
        """
        prompt = QUIZ_JUDGE_PROMPT.format(
            question=question.get("question", ""),
            question_type=question.get("type", "choice"),
            correct_answer=question.get("answer", ""),
            user_answer=user_answer,
        )

        messages = [
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = await self.provider.chat(messages)
        result = self._parse_json(response)

        if result and "correct" in result:
            progress = context_manager.get_quiz_progress()
            if result["correct"]:
                progress["correct_count"] = progress.get("correct_count", 0) + 1
            context_manager.set_quiz_progress(progress)

        return result or {"correct": False, "explanation": "评判失败"}

    def next_question(self) -> Optional[dict]:
        """获取下一题"""
        progress = context_manager.get_quiz_progress()
        questions = progress.get("questions", [])
        current = progress.get("current_index", 0)

        if current < len(questions):
            question = questions[current]
            progress["current_index"] = current + 1
            context_manager.set_quiz_progress(progress)
            return question

        return None

    def get_progress(self) -> dict:
        """获取测验进度"""
        return context_manager.get_quiz_progress()

    def _parse_questions(self, text: str) -> list[dict]:
        """解析 LLM 返回的题目 JSON"""
        try:
            start = text.index("[")
            end = text.rindex("]") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return []

    def _parse_json(self, text: str) -> dict:
        """解析 JSON"""
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return {}
