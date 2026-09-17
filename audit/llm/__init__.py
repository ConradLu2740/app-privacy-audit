"""LLM Provider 抽象层。

对外只暴露接口、消息类型与工厂函数，业务模块不直接依赖具体厂商实现。
"""

from audit.llm.base import (
    ChatMessage,
    LLMError,
    LLMProvider,
    LLMResponseError,
    Usage,
    parse_json_loose,
)
from audit.llm.factory import ConfigError, build_provider, load_config
from audit.llm.fake import FakeProvider
from audit.llm.openai_compat import OpenAICompatibleProvider, normalize_root
from audit.llm.proma_cloud import PromaCloudProvider

__all__ = [
    "ChatMessage",
    "ConfigError",
    "FakeProvider",
    "LLMError",
    "LLMProvider",
    "LLMResponseError",
    "OpenAICompatibleProvider",
    "PromaCloudProvider",
    "Usage",
    "build_provider",
    "load_config",
    "normalize_root",
    "parse_json_loose",
]
