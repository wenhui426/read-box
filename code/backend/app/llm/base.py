"""
LLM Provider 抽象基类

定义统一的 AI 模型调用接口。
所有 Provider（OpenAI、Claude、Ollama 等）必须实现此接口。
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProviderConfig:
    """
    LLM Provider 配置

    从环境变量或字典初始化，支持多种后端模型。
    """
    provider_type: str = ""              # Provider 类型：openai / claude / ollama
    api_key: str = ""                    # API 密钥
    api_base: str = ""                   # API 地址
    model: str = "gpt-4o"               # 模型名称
    max_tokens: int = 4096              # 最大输出 token 数
    temperature: float = 0.7            # 生成温度

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        """从环境变量读取配置"""
        return cls(
            provider_type=os.getenv("LLM_PROVIDER", "openai"),
            api_key=os.getenv("LLM_API_KEY", ""),
            api_base=os.getenv("LLM_API_BASE", "https://api.openai.com/v1"),
            model=os.getenv("LLM_MODEL", "gpt-4o"),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        )


class LLMProvider(ABC):
    """
    LLM Provider 抽象基类

    所有 AI 模型调用必须通过此接口。
    """

    def __init__(self, config: ProviderConfig) -> None:
        """
        初始化 Provider

        Args:
            config: Provider 配置
        """
        self.config = config

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        """
    调用 LLM 聊天接口

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数（可覆盖 config 中的默认值）

        Returns:
            模型返回的文本内容
        """
        pass
