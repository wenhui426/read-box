"""
LLM Provider 单元测试

测试 Provider 抽象层的接口一致性。
使用 mock HTTP 服务器模拟 LLM API 响应。
"""

import pytest
from app.llm.base import ProviderConfig, LLMProvider


class TestProviderConfig:
    """Provider 配置测试"""

    def test_from_env_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试默认配置"""
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        config = ProviderConfig.from_env()
        assert config.provider_type == "openai"
        assert config.model == "gpt-4o"

    def test_from_env_custom(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试自定义环境变量配置"""
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        monkeypatch.setenv("LLM_MODEL", "llama3")
        monkeypatch.setenv("LLM_API_BASE", "http://localhost:11434/v1")
        config = ProviderConfig.from_env()
        assert config.provider_type == "ollama"
        assert config.model == "llama3"
        assert config.api_base == "http://localhost:11434/v1"

    def test_abstract_provider_cannot_be_instantiated(self) -> None:
        """测试抽象类不能直接实例化"""
        with pytest.raises(TypeError):
            LLMProvider(ProviderConfig())  # type: ignore
