"""OpenAI 兼容 Provider 通用底座。

覆盖任意提供 /v1/chat/completions 的服务，包括：
  - Proma Cloud（见 proma_cloud.py）
  - OpenAI 官方
  - 本地 OpenAI 兼容推理服务（如 Ollama 的 /v1 接口）

切换服务只需改配置里的 base_url 与 model，不改业务代码。
"""

from __future__ import annotations

import time

import httpx

from audit.llm.base import ChatMessage, LLMError, LLMProvider, Usage

#: 429 / 502 重试退避（秒）
RETRY_BACKOFF = (1.0, 3.0, 9.0)


def normalize_root(base_url: str) -> str:
    """把 base_url 归一化成根域名。

    Proma Cloud 的凭据历史上返回过带 /api/v1 后缀的地址，
    直接拼 /v1/chat/completions 会得到 /api/v1/v1/... 而 404。
    归一化是幂等的。
    """
    return base_url.rstrip("/").removesuffix("/api/v1")


class OpenAICompatibleProvider(LLMProvider):
    """通过 OpenAI Chat Completions 协议调用任意兼容端点。"""

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key: str,
        provider_name: str = "openai-compatible",
        timeout: float = 120.0,
    ) -> None:
        super().__init__(model)
        self.root = normalize_root(base_url)
        self.api_key = api_key
        self._provider_name = provider_name
        self.timeout = timeout

    @property
    def name(self) -> str:
        return self._provider_name

    @property
    def chat_url(self) -> str:
        # 根域名统一拼 /v1/chat/completions；
        # 若调用方传入的已是 .../v1 形式，则直接补 /chat/completions。
        if self.root.endswith("/v1"):
            return f"{self.root}/chat/completions"
        return f"{self.root}/v1/chat/completions"

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        payload: dict[str, object] = {
            "model": self.model,
            "messages": self._build_messages(messages, system),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        data = self._post(payload)
        return self._extract_content(data)

    # -- 内部 -------------------------------------------------------------

    @staticmethod
    def _build_messages(
        messages: list[ChatMessage], system: str | None
    ) -> list[dict[str, str]]:
        built: list[dict[str, str]] = []
        if system:
            built.append({"role": "system", "content": system})
        built.extend(m.to_dict() for m in messages)
        return built

    def _post(self, payload: dict[str, object]) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None

        for attempt, delay in enumerate((0.0, *RETRY_BACKOFF)):
            if delay:
                time.sleep(delay)
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(self.chat_url, json=payload, headers=headers)
            except httpx.HTTPError as exc:  # 网络层问题，可重试
                last_error = exc
                continue

            if resp.status_code in (429, 502):
                last_error = LLMError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                continue
            if resp.status_code >= 400:
                # 其余 4xx 不重试
                raise LLMError(
                    f"{self.name} 调用失败 HTTP {resp.status_code}: {resp.text[:500]}"
                )

            try:
                data = resp.json()
            except ValueError as exc:
                raise LLMError(f"{self.name} 返回非 JSON：{resp.text[:300]}") from exc

            self._record_usage(data)
            return data

        raise LLMError(f"{self.name} 重试 {len(RETRY_BACKOFF)} 次后仍失败：{last_error}")

    def _record_usage(self, data: dict) -> None:
        """累计 token 消耗。

        推理模型的输出预算可能被思考链占用（某些平台下 output_tokens 为 0），
        因此 completion_tokens 作为主口径，缺失时退回 output_tokens。
        """
        usage = data.get("usage") or {}
        prompt = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        completion = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        self.usage = self.usage + Usage(
            prompt_tokens=int(prompt), completion_tokens=int(completion)
        )

    @staticmethod
    def _extract_content(data: dict) -> str:
        try:
            choice = data["choices"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"响应缺少 choices 字段：{str(data)[:300]}") from exc

        message = choice.get("message") or {}
        content = message.get("content")
        if not content:
            # 推理模型可能把内容放在 reasoning_content，或返回空
            content = message.get("reasoning_content")
        if not content:
            raise LLMError(f"响应内容为空：{str(data)[:300]}")
        return content
