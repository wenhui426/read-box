"""
问答 API 路由

提供基于书籍内容的问答 Web 接口。
支持流式输出（SSE）、上下文追问、清空历史。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from starlette.requests import Request

from app.agents.qa_agent import QAAgent
from app.context.manager import context_manager
from app.database import get_db
from app.llm import create_provider
from app.llm.base import ProviderConfig

router = APIRouter(prefix="/api/qa", tags=["qa"])


async def _get_agent() -> QAAgent:
    """获取 QAAgent 实例（从数据库读取 LLM 配置）"""
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
    return QAAgent(provider=provider)


@router.post("/{book_id}/ask")
async def ask_question(book_id: int, request: Request) -> StreamingResponse:
    """
    提问（流式返回）

    基于当前书籍内容回答问题，以 SSE 格式流式输出。
    支持多轮对话（上下文保持在 ContextManager 中）。
    """
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    agent = await _get_agent()

    async def event_stream():
        """生成 SSE 事件流（JSON 编码每块数据，防止换行符被 SSE 协议吃掉）"""
        import json as _json
        async for chunk in agent.ask(book_id, question):
            encoded = _json.dumps({"t": chunk}, ensure_ascii=False)
            yield f"data: {encoded}\n\n"
        yield "data: {\"t\": \"[DONE]\"}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{book_id}/clear")
async def clear_context(book_id: int) -> dict:
    """
    清空对话历史

    切换书籍或用户主动清空时调用。
    """
    agent = await _get_agent()
    await agent.clear_context(book_id)
    # 同时清空 SQLite 中的历史
    try:
        db = await get_db()
        await db.execute("DELETE FROM chat_history WHERE book_id = ?", (book_id,))
        await db.commit()
        await db.close()
    except Exception:
        pass
    return {"status": "cleared"}


@router.get("/{book_id}/history")
async def get_history(book_id: int) -> dict:
    """
    获取对话历史

    先尝试从内存 ContextManager 读取，如果为空则从 SQLite 恢复。
    后端重启后对话历史不会丢失。
    """
    # 从内存读取
    if context_manager.current_book_id == book_id:
        history = context_manager.get_history()
        if history:
            return {"history": history}

    # 内存中没有（如后端重启），从 SQLite 恢复
    try:
        db = await get_db()
        rows = await db.execute_fetchall(
            "SELECT role, content FROM chat_history WHERE book_id = ? ORDER BY id ASC",
            (book_id,),
        )
        await db.close()
        history = [{"role": r[0], "content": r[1]} for r in rows]

        # 恢复到内存
        if history:
            context_manager.set_book(book_id)
            for msg in history:
                context_manager.add_message(msg["role"], msg["content"])

        return {"history": history}
    except Exception:
        return {"history": []}
