"""
应用配置接口

提供应用级别的配置查询功能。
当前返回数据库版本和应用版本号，后续可扩展。
"""

from fastapi import APIRouter

# 创建配置路由，挂载到 /api 路径
router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
async def get_config() -> dict:
    """
    获取应用配置

    返回数据库版本和应用版本号。
    前端启动时调用此接口确认后端就绪。
    """
    return {
        "db_version": 1,          # 数据库 schema 版本
        "app_version": "0.1.0",   # 应用版本
    }
