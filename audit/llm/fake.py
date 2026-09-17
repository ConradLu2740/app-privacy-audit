"""FakeProvider —— 测试与离线回放。

用途有二：
  1. 单元测试：给定输入，返回可预期的固定响应
  2. 无网络复现：专家核查源码时无需 API key 即可跑通端到端流程

匹配策略：按调用序号顺序返回，或用 key 子串匹配。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audit.llm.base import ChatMessage, LLMError, LLMProvider


class FakeProvider(LLMProvider):
    """返回预设响应的 provider。"""

    def __init__(
        self,
        responses: list[Any] | None = None,
        *,
        response_file: str | Path | None = None,
        model: str = "fake",
    ) -> None:
        super().__init__(model)
        if response_file is not None:
            payload = json.loads(Path(response_file).read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                # {"task_name": [...]} 形式，按 key 匹配
                self._by_key: dict[str, Any] = payload
                self._queue: list[Any] = []
            else:
                self._by_key = {}
                self._queue = list(payload)
        else:
            self._by_key = {}
            self._queue = list(responses or [])

        self.calls: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        return "fake"

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        self.calls.append(
            {
                "messages": [m.to_dict() for m in messages],
                "system": system,
                "json_mode": json_mode,
            }
        )

        # 1) 按 key 匹配：system 或最后一条 user 消息里出现的 key。
        #    多个 key 同时命中时取最长 key，避免短 key（如政策引证片段）
        #    抢占语义判定等更长特征的响应。
        haystack = (system or "") + "\n" + "\n".join(m.content for m in messages)
        best_key = None
        for key in self._by_key:
            if key in haystack and (best_key is None or len(key) > len(best_key)):
                best_key = key
        if best_key is not None:
            return self._render(self._by_key[best_key])

        # 2) 顺序出队
        if self._queue:
            return self._render(self._queue.pop(0))

        # 3) 队列耗尽：返回空数组，让上层走「无命中」分支而不是崩溃
        if json_mode:
            return "[]"
        raise LLMError("FakeProvider 无可用响应，且非 JSON 模式")

    @staticmethod
    def _render(value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
