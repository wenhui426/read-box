# LLM Provider 抽象层
# 提供统一的 AI 模型调用接口，支持多种后端
# 遵循宪法：所有 AI 调用必须通过此层，不得直接调用模型 API

import os
from typing import Optional

from app.llm.base import LLMProvider, ProviderConfig
from app.llm.openai_provider import OpenAIProvider

# 默认 Provider 实例（由 get_default_provider 延迟初始化）
_default_provider: Optional[LLMProvider] = None


def create_provider(config: Optional[ProviderConfig] = None) -> LLMProvider:
    """
    创建 LLM Provider 实例

    可通过参数传入配置，或从环境变量读取。

    Args:
        config: Provider 配置。为 None 时从环境变量读取。

    Returns:
        配置好的 LLMProvider 实例
    """
    if config is None:
        config = ProviderConfig.from_env()

    if config.provider_type == "openai" or not config.provider_type:
        return OpenAIProvider(config)
    elif config.provider_type == "claude":
        from app.llm.claude_provider import ClaudeProvider
        return ClaudeProvider(config)
    elif config.provider_type == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        return OllamaProvider(config)
    else:
        raise ValueError(f"不支持的 Provider 类型: {config.provider_type}")


def get_default_provider() -> LLMProvider:
    """
    获取默认 LLM Provider 实例（单例）

    从环境变量初始化。数据库配置由 API 路由层读取后注入 Agent。
    """
    global _default_provider
    if _default_provider is None:
        _default_provider = create_provider()
    return _default_provider


__all__ = [
    "LLMProvider",
    "ProviderConfig",
    "create_provider",
    "get_default_provider",
]
