"""按配置构建 provider。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from audit.llm.base import LLMProvider
from audit.llm.fake import FakeProvider
from audit.llm.openai_compat import OpenAICompatibleProvider
from audit.llm.proma_cloud import PromaCloudProvider

DEFAULT_CONFIG_PATHS = ("config.yaml", "config.yml")

#: provider=fake 时的默认固定响应文件（仓库内自带，用于离线复现）
DEFAULT_FAKE_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "fake_responses.json"


def _default_fake_fixture() -> Path | None:
    return DEFAULT_FAKE_FIXTURE if DEFAULT_FAKE_FIXTURE.is_file() else None


class ConfigError(ValueError):
    """配置缺失或非法。"""


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """载入配置文件；找不到时返回空配置（依赖环境变量）。"""
    candidates = [Path(path)] if path else [Path(p) for p in DEFAULT_CONFIG_PATHS]
    for candidate in candidates:
        if candidate.is_file():
            data = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                raise ConfigError(f"{candidate} 顶层必须是映射")
            return data
    return {}


def build_provider(
    config: dict[str, Any] | None = None,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    """构建 LLM provider。

    优先级：显式参数 > 配置文件 > 环境变量 > 默认值。
    """
    cfg = config or {}
    llm_cfg = cfg.get("llm") or {}

    chosen = (
        provider
        or os.environ.get("AUDIT_LLM_PROVIDER")
        or llm_cfg.get("provider")
        or "proma-cloud"
    )
    chosen_model = model or llm_cfg.get("model")

    if chosen == "fake":
        fixture = llm_cfg.get("fake_responses") or _default_fake_fixture()
        if fixture:
            return FakeProvider(response_file=fixture)
        return FakeProvider()

    if chosen == "proma-cloud":
        return PromaCloudProvider(
            api_key=llm_cfg.get("api_key"),
            base_url=llm_cfg.get("base_url"),
            model=chosen_model,
        )

    if chosen in ("openai-compatible", "openai", "custom"):
        api_key = (
            llm_cfg.get("api_key")
            or os.environ.get("AUDIT_LLM_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        if not api_key:
            raise ConfigError(f"{chosen} 需要 api_key（配置或环境变量）")
        base_url = llm_cfg.get("base_url") or os.environ.get("AUDIT_LLM_BASE_URL")
        if not base_url:
            raise ConfigError(f"{chosen} 需要 base_url")
        return OpenAICompatibleProvider(
            model=chosen_model or "gpt-4o-mini",
            base_url=base_url,
            api_key=api_key,
            provider_name=chosen,
        )

    raise ConfigError(
        f"未知 provider：{chosen}（可选 proma-cloud / openai-compatible / fake）"
    )
