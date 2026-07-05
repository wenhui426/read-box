"""
提炼 API 路由

提供 AI 提炼的 Web 接口：
- 启动全书提炼
- 查询提炼进度
- 查看单章结果
- 导出 Markdown 笔记
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.agents.digest_agent import DigestAgent
from app.database import get_db
from app.llm import create_provider
from app.llm.base import ProviderConfig

# 创建提炼路由，挂载到 /api/digest 路径
router = APIRouter(prefix="/api/digest", tags=["digest"])


async def _get_agent() -> DigestAgent:
    """
    获取 DigestAgent 实例（含 LLM 配置）

    从数据库读取用户保存的 LLM 配置，注入到 Agent 中。
    若数据库有配置则使用数据库配置，否则使用环境变量。
    """
    provider = None
    try:
        db = await get_db()
        # 从 app_config 表读取 LLM 配置
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
            # 有配置，合并环境变量默认值
            env = ProviderConfig.from_env()
            for field in ["provider_type", "api_base", "model"]:
                if field not in config_dict or not config_dict[field]:
                    config_dict[field] = getattr(env, field, "")
            provider = create_provider(ProviderConfig(**config_dict))
    except Exception:
        pass  # 兜底：使用环境变量配置

    return DigestAgent(provider=provider)


@router.post("/{book_id}/start")
async def start_digest(book_id: int) -> dict:
    """
    启动全书提炼

    异步任务：后端创建提炼记录后立即返回，前端通过 /status 轮询进度。
    """
    agent = await _get_agent()
    result = await agent.digest_book(book_id)
    return result


@router.post("/{book_id}/chapters/{chapter_id}")
async def digest_chapter(book_id: int, chapter_id: int) -> dict:
    """
    单章提炼

    仅处理指定的章节，结果增量写入数据库。
    """
    agent = await _get_agent()
    return await agent.digest_single_chapter(book_id, chapter_id)


@router.get("/{book_id}/status")
async def get_digest_status(book_id: int) -> dict:
    """
    查询提炼进度

    返回当前提炼任务的进度信息，前端据此展示进度条。
    """
    db = await get_db()
    rows = await db.execute_fetchall(
        """
        SELECT id, status, total_chapters, processed_chapters, created_at
        FROM digests
        WHERE book_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (book_id,),
    )
    await db.close()

    if not rows:
        return {"digest_id": None, "status": "none", "total": 0, "processed": 0}

    row = rows[0]
    return {
        "digest_id": row[0],
        "status": row[1],
        "total": row[2],
        "processed": row[3],
        "created_at": row[4],
    }


@router.get("/{book_id}/chapters/{chapter_id}")
async def get_chapter_digest(book_id: int, chapter_id: int) -> dict:
    """
    获取单章提炼结果

    返回指定章节的摘要、概念列表和金句列表。
    """
    db = await get_db()
    rows = await db.execute_fetchall(
        """
        SELECT cd.id, cd.summary
        FROM chapter_digests cd
        JOIN digests d ON cd.digest_id = d.id
        WHERE cd.chapter_id = ? AND d.book_id = ?
        ORDER BY cd.created_at DESC
        LIMIT 1
        """,
        (chapter_id, book_id),
    )
    if not rows:
        await db.close()
        return {"summary": "", "concepts": [], "quotes": []}

    cd_id, summary = rows[0]

    # 获取概念
    concepts = await db.execute_fetchall(
        "SELECT term, explanation FROM key_concepts WHERE chapter_digest_id = ? ORDER BY sort_order",
        (cd_id,),
    )
    concepts_list = [{"term": r[0], "explanation": r[1]} for r in concepts]

    # 获取金句
    quotes = await db.execute_fetchall(
        "SELECT quote, reason FROM golden_quotes WHERE chapter_digest_id = ? ORDER BY sort_order",
        (cd_id,),
    )
    quotes_list = [{"quote": r[0], "reason": r[1]} for r in quotes]

    await db.close()

    return {
        "summary": summary,
        "concepts": concepts_list,
        "quotes": quotes_list,
    }


@router.get("/{book_id}/export")
async def export_digest(book_id: int) -> PlainTextResponse:
    """
    导出全书读书笔记（Markdown 格式）

    返回完整的 Markdown 文件，包含目录、各章摘要、概念汇总和金句合集。
    """
    agent = _get_agent()
    markdown = await agent.export_markdown(book_id)
    if markdown is None:
        raise HTTPException(status_code=404, detail="书籍不存在或无提炼结果")

    return PlainTextResponse(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=reading_notes_{book_id}.md"},
    )
