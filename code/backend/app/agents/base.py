"""
Agent 抽象基类

所有 AI Agent 必须继承此类。
通过构造函数注入 LLM Provider，遵循宪法"LLM Provider 抽象层"设计。
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.llm.base import LLMProvider


class BaseAgent(ABC):
    """
    Agent 基类

    提供 LLM Provider 注入和通用方法。
    子类只需实现具体的 Agent 逻辑。
    """

    def __init__(self, provider: Optional[LLMProvider] = None) -> None:
        """
        初始化 Agent

        Args:
            provider: LLM Provider 实例。如果为 None，由全局配置自动选择。
        """
        self._provider = provider

    @property
    def provider(self) -> LLMProvider:
        """获取当前使用的 LLM Provider"""
        if self._provider is None:
            # 从全局配置获取默认 Provider
            from app.llm import get_default_provider
            self._provider = get_default_provider()
        return self._provider

    @provider.setter
    def provider(self, provider: LLMProvider) -> None:
        """设置 LLM Provider"""
        self._provider = provider

    @abstractmethod
    async def run(self, **kwargs) -> dict:
        """
        执行 Agent 任务

        Args:
            **kwargs: 任务参数

        Returns:
            任务结果字典
        """
        pass
