# 共享上下文模块

# 问答 Agent 和陪练 Agent 共用的上下文管理器
# 在内存中维护当前会话状态，切换书籍时自动清空

from .manager import context_manager

__all__ = ["context_manager"]
