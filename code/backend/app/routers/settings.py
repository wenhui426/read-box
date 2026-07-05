"""
应用设置 API 路由

提供 LLM Provider 配置的读写接口。
设置存储在 SQLite app_config 表中。
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])

# LLM 配置项的默认值
DEFAULT_LLM_CONFIG = {
    "llm_provider": "openai",
    "llm_api_key": "",
    "llm_api_base": "https://api.deepseek.com",
    "llm_model": "",
    "llm_max_tokens": "4096",
    "llm_temperature": "0.7",
}


@router.get("/llm")
async def get_llm_settings() -> dict:
    """获取 LLM 配置"""
    db = await get_db()
    config = {}
    for key in DEFAULT_LLM_CONFIG:
        rows = await db.execute_fetchall(
            "SELECT value FROM app_config WHERE key = ?", (key,)
        )
        config[key] = rows[0][0] if rows else DEFAULT_LLM_CONFIG[key]
    await db.close()
    return config


@router.post("/llm")
async def save_llm_settings(body: dict) -> JSONResponse:
    """保存 LLM 配置"""
    db = await get_db()
    for key, value in body.items():
        if key in DEFAULT_LLM_CONFIG:
            await db.execute(
                "INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)",
                (key, str(value)),
            )
    await db.commit()
    await db.close()
    return JSONResponse(content={"status": "saved"})
