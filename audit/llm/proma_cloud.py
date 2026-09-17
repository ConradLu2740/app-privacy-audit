"""Proma Cloud Provider —— 开发与演示的默认实现。

凭据获取（Agent 侧）：mcp__proma-cloud__get_credentials 返回 { apiKey, baseUrl }。
用户侧复现：在 config.yaml 里填自己的 base_url 与 api_key，或用环境变量
  AUDIT_LLM_BASE_URL / AUDIT_LLM_API_KEY。

数据流向披露：本 provider 会把被测应用的隐私政策文本发送至第三方服务。
不发送抓包载荷、不发送个人信息、不发送 APK。见设计文档 4.4 节。
"""

from __future__ import annotations

import os

from audit.llm.openai_compat import OpenAICompatibleProvider

DEFAULT_BASE_URL = "https://api.proma.cool"
#: 默认模型。中文政策文本结构化抽取，选用中文能力较强的模型。
#: 可用模型清单请调 GET /v1/models 查询，不要依赖此处硬编码值。
DEFAULT_MODEL = "glm-5.3"

ENV_BASE_URL = "AUDIT_LLM_BASE_URL"
ENV_API_KEY = "AUDIT_LLM_API_KEY"
ENV_MODEL = "AUDIT_LLM_MODEL"


class PromaCloudProvider(OpenAICompatibleProvider):
    """通过 Proma Cloud 的 OpenAI 兼容端点调用模型。"""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get(ENV_API_KEY, "")
        if not resolved_key:
            raise ValueError(
                f"缺少 Proma Cloud 凭据。请设置环境变量 {ENV_API_KEY}，"
                "或在 config.yaml 中填写 llm.api_key。"
            )
        super().__init__(
            model=model or os.environ.get(ENV_MODEL, DEFAULT_MODEL),
            base_url=base_url or os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL),
            api_key=resolved_key,
            provider_name="proma-cloud",
        )
