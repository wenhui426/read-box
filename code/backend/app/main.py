"""
Read-Box 后端服务入口

创建 FastAPI 应用实例，配置 CORS 中间件，注册 API 路由。
应用启动时自动初始化 SQLite 数据库。
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from dotenv import load_dotenv  # 加载 .env 环境变量
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入数据库初始化函数
from app.database import init_db

# 导入 API 路由
from app.routers import config, books, digest, qa, quiz, settings, dashboard, highlights, reading

# 加载环境变量配置（数据库路径、端口等）
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理

    - 启动时（yield 前）：初始化数据库表结构
    - 关闭时（yield 后）：可在此处添加清理逻辑
    """
    # 应用启动：初始化 SQLite 数据库
    await init_db()
    yield
    # 应用关闭：可在此处添加清理逻辑


# 创建 FastAPI 应用实例
app = FastAPI(
    title="Read-Box API",       # API 文档标题
    version="0.1.0",            # 当前版本
    lifespan=lifespan,          # 注册生命周期处理器
)

# 配置跨域请求（CORS）
# 允许前端开发服务器（Vite）和 Tauri 桌面应用访问后端 API
app.add_middleware(
    CORSMiddleware,
    # 开发模式下允许所有来源（CORS 不拦截）
    # 生产环境中应限制为具体的前端地址
    allow_origins=["*"],
    allow_credentials=True,      # 允许携带凭据
    allow_methods=["*"],         # 允许所有 HTTP 方法
    allow_headers=["*"],         # 允许所有请求头
)

# 注册 API 路由
# 每个路由模块注册到对应路径前缀
app.include_router(config.router)
app.include_router(books.router)
app.include_router(digest.router)
app.include_router(qa.router)
app.include_router(quiz.router)
app.include_router(settings.router)
app.include_router(dashboard.router)
app.include_router(highlights.router)
app.include_router(reading.router)


@app.get("/api/health")
async def health_check() -> dict:
    """
    健康检查接口

    前端和 Tauri 壳层通过此接口确认后端服务是否正常运行。
    启动时 Tauri 会轮询此接口，直到返回 {"status": "ok"}。
    """
    return {
        "status": "ok",                                   # 服务状态
        "version": "0.1.0",                               # 后端版本号
        "timestamp": datetime.now(timezone.utc).isoformat(),  # 当前 UTC 时间
    }
