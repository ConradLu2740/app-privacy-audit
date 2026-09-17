"""LLM Provider 抽象层。

设计目标：业务代码只依赖本接口，不依赖任何具体厂商。
见 docs/design/llm-compliance-engine.md 第 4 节。
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class LLMError(RuntimeError):
    """LLM 调用失败。"""


class LLMResponseError(LLMError):
    """返回内容不符合预期（如无法解析为 JSON）。"""


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.prompt_tokens + other.prompt_tokens,
            self.completion_tokens + other.completion_tokens,
        )


class LLMProvider(ABC):
    """LLM 提供方统一接口。"""

    def __init__(self, model: str) -> None:
        self.model = model
        self.usage = Usage()

    @property
    @abstractmethod
    def name(self) -> str:
        """提供方标识，用于报告与日志。"""

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """返回助手回复的纯文本。"""

    # -- 便捷方法 ---------------------------------------------------------

    def chat_json(
        self,
        messages: list[ChatMessage],
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        retries: int = 1,
    ) -> Any:
        """要求返回 JSON 并解析，解析失败时追加修正指令重试。

        推理型模型偶尔会先输出分析过程再给结论，或干脆不输出 JSON。
        重试时把上一次的返回作为 assistant 消息回灌，并追加一条明确的
        user 修正指令，通常一次就能拿到合法 JSON。
        """
        conversation = list(messages)
        last_raw = ""

        for attempt in range(retries + 1):
            raw = self.chat(
                conversation,
                system=system,
                temperature=0.0,
                max_tokens=max_tokens,
                json_mode=True,
            )
            try:
                return parse_json_loose(raw)
            except LLMResponseError:
                last_raw = raw
                if attempt >= retries:
                    break
                conversation = list(messages) + [
                    ChatMessage(role="assistant", content=raw[:2000]),
                    ChatMessage(
                        role="user",
                        content=(
                            "你的上一次回复不是合法 JSON。"
                            "请只输出一个 JSON 对象，不要任何解释文字、"
                            "不要 Markdown 代码块标记、不要分析过程。"
                        ),
                    ),
                ]

        raise LLMResponseError(f"无法从模型返回中解析 JSON：{last_raw[:300]}")


def parse_json_loose(raw: str) -> Any:
    """从模型返回文本中尽力提取 JSON。

    处理三种常见形态：纯 JSON、```json 围栏、前后有说明文字。
    """
    text = raw.strip()

    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 退一步：截取第一个 { 或 [ 到最后一个 } 或 ]
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise LLMResponseError(f"无法从模型返回中解析 JSON：{raw[:300]}")
