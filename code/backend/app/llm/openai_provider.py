"""
OpenAI 兼容 LLM Provider

支持所有 OpenAI 兼容的 API 服务：
- OpenAI
- DeepSeek
- 通义千问
- 各种代理中转服务
"""

import httpx
from app.llm.base import LLMProvider, ProviderConfig


class OpenAIProvider(LLMProvider):
    """OpenAI 兼容 API Provider"""

    def __init__(self, config: ProviderConfig) -> None:
        """初始化 OpenAI Provider"""
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.api_base,
                timeout=httpx.Timeout(120.0),
            )
        return self._client

    async def chat(self, messages: list[dict], **kwargs) -> str:
        """
        调用 OpenAI 兼容的聊天 API

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            模型回复文本
        """
        client = await self._get_client()

        # 合并参数：kwargs 覆盖 config 默认值
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)
        model = kwargs.get("model", self.config.model)

        response = await client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
