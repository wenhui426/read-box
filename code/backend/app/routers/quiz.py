"""
陪练 API 路由

提供章节测验、全书考试、自适应陪练的 Web 接口。
"""

from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from app.agents.quiz_agent import QuizAgent
from app.context.manager import context_manager
from app.database import get_db
from app.llm import create_provider
from app.llm.base import ProviderConfig

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


async def _get_agent() -> QuizAgent:
    """获取 QuizAgent 实例（从数据库读取 LLM 配置）"""
    provider = None
    try:
        db = await get_db()
        config_map = {
            "llm_provider": "provider_type",
            "llm_api_key": "api_key",
            "llm_api_base": "api_base",
            "llm_model": "model",
            "llm_max_tokens": "max_tokens",
            "llm_temperature": "temperature",
        }
        config_dict: dict[str, str | int | float] = {}
        for db_key, conf_key in config_map.items():
            rows = await db.execute_fetchall(
                "SELECT value FROM app_config WHERE key = ?", (db_key,)
            )
            if rows and rows[0][0]:
                raw = rows[0][0]
                if db_key == "llm_max_tokens":
                    config_dict[conf_key] = int(raw)
                elif db_key == "llm_temperature":
                    config_dict[conf_key] = float(raw)
                else:
                    config_dict[conf_key] = raw
        await db.close()
        if config_dict.get("api_key"):
            env = ProviderConfig.from_env()
            for field in ["provider_type", "api_base", "model"]:
                if field not in config_dict or not config_dict[field]:
                    config_dict[field] = getattr(env, field, "")
            provider = create_provider(ProviderConfig(**config_dict))
    except Exception:
        pass
    return QuizAgent(provider=provider)


@router.post("/{book_id}/start")
async def start_quiz(book_id: int, request: Request) -> dict:
    """
    启动测验

    两种模式：
    - chapter_id 有值：章节测验
    - chapter_id 为 null：全书考试
    body: {chapter_id?: int, count: int, mode?: string}
    """
    body = await request.json()
    chapter_id = body.get("chapter_id")
    count = body.get("count", 5)
    mode = body.get("mode", "chapter" if chapter_id else "exam")

    agent = await _get_agent()
    context_manager.set_book(book_id)

    if chapter_id:
        questions = await agent.start_chapter_quiz(book_id, chapter_id, count)
    else:
        questions = await agent.start_exam(book_id, count)

    return {"questions": questions, "total": len(questions), "mode": mode}


@router.post("/{book_id}/answer")
async def submit_answer(book_id: int, request: Request) -> dict:
    """
    提交答案并评判

    body: {question: dict, answer: str}
    """
    body = await request.json()
    question = body.get("question")
    answer = body.get("answer", "")

    if not question or not answer:
        raise HTTPException(status_code=400, detail="需要题目和答案")

    agent = await _get_agent()
    result = await agent.judge_answer(question, answer)

    progress = agent.get_progress()
    return {
        "correct": result.get("correct", False),
        "explanation": result.get("explanation", ""),
        "current": progress.get("current_index", 0),
        "total": progress.get("total_count", 0),
        "correct_count": progress.get("correct_count", 0),
    }


@router.get("/{book_id}/next")
async def next_question(book_id: int) -> dict:
    """获取下一题"""
    agent = await _get_agent()
    question = agent.next_question()
    if question is None:
        progress = agent.get_progress()
        return {"done": True, "correct": progress.get("correct_count", 0), "total": progress.get("total_count", 0)}
    return {"question": question}


@router.get("/{book_id}/progress")
async def get_progress(book_id: int) -> dict:
    """查询测验进度"""
    agent = await _get_agent()
    return agent.get_progress()
