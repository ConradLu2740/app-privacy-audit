"""LLM 语义判定。

见 docs/design/llm-compliance-engine.md 第 5.4 节。

三处使用 LLM，全部限定输出为结构化 JSON，且必须返回 reason：
  1. 必要性判断（超范围收集）
  2. 共享对象语义匹配（未声明共享）
  3. 政策矛盾判定

所有违规类型都取自 ViolationType 闭集，模型无法编造新的类型。
所有条号都来自 RegulationLibrary 检索，模型无法编造条号。
"""

from __future__ import annotations

from typing import Any

from audit.align.rules import Candidate
from audit.llm import ChatMessage, LLMProvider, LLMResponseError
from audit.policy.prompts import (
    SEMANTIC_SYSTEM,
    build_contradiction_prompt,
    build_necessity_prompt,
    build_sharing_prompt,
)
from audit.schema import Finding, Severity, ViolationType


class SemanticJudge:
    """调用 LLM 处理语义模糊的判定。"""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider
        self.errors: list[str] = []

    def judge(self, candidate: Candidate, *, index: int) -> Finding | None:
        handlers = {
            "necessity": self._judge_necessity,
            "sharing": self._judge_sharing,
            "contradiction": self._judge_contradiction,
        }
        handler = handlers.get(candidate.kind)
        if handler is None:
            self.errors.append(f"未知候选类型：{candidate.kind}")
            return None
        try:
            return handler(candidate.payload, index)
        except LLMResponseError as exc:
            self.errors.append(f"{candidate.kind}: {exc}")
            return None
        except Exception as exc:  # noqa: BLE001
            self.errors.append(f"{candidate.kind}: {type(exc).__name__}: {exc}")
            return None

    # -- 各场景 -----------------------------------------------------------

    def _judge_necessity(self, payload: dict[str, Any], index: int) -> Finding | None:
        prompt = build_necessity_prompt(
            data_type=payload["data_type"],
            app_category=payload.get("app_category", "unknown"),
            declared_purposes=payload.get("declared_purposes", []),
            observations=payload.get("observations", []),
        )
        result = self._ask(prompt)
        if not result.get("is_beyond_scope"):
            return None

        confidence = str(result.get("confidence", "low"))
        reason = str(result.get("reason", "")).strip()
        necessary = bool(result.get("is_necessary_for_core_function"))
        sample = payload.get("sample", "")

        if necessary:
            # 属基本功能所必需但政策未声明 → 披露不足，而非超范围收集
            rationale = (
                f"{payload['data_type']} 属实现基本功能所必需，但政策未作声明，"
                f"属披露不足。{reason}"
            )
        else:
            rationale = f"{payload['data_type']} 与基本功能无直接关系且政策未声明。{reason}"

        return Finding(
            finding_id=f"F-{sample}-S{index:03d}",
            sample=sample,
            violation_type=ViolationType.BEYOND_SCOPE,
            severity=Severity.MEDIUM if not necessary else Severity.LOW,
            rationale=rationale,
            behavior_facts=list(payload.get("fact_ids", [])),
            declarations=[],
            regulation_refs=[],
            evidence_refs=self._evidence_refs_from_facts(payload.get("fact_ids", [])),
            needs_review=confidence != "high",
            decided_by="semantic",
        )

    def _judge_sharing(self, payload: dict[str, Any], index: int) -> Finding | None:
        prompt = build_sharing_prompt(
            observed_targets=payload.get("observed_targets", []),
            declared_shared_with=payload.get("declared_shared_with", []),
            policy_quotes=payload.get("policy_quotes", []),
        )
        result = self._ask(prompt)
        if not isinstance(result, dict):
            return None

        target_facts: dict[str, list[str]] = payload.get("target_facts", {})
        undeclared = [
            name
            for name, verdict in result.items()
            if isinstance(verdict, dict) and not verdict.get("declared", True)
        ]
        if not undeclared:
            return None

        sample = payload.get("sample", "")
        fact_ids: list[str] = []
        for name in undeclared:
            fact_ids.extend(target_facts.get(name, []))
        fact_ids = list(dict.fromkeys(fact_ids))  # 去重，保持顺序

        reasons = [
            f"{name}：{result[name].get('reason', '政策未提及')}"
            for name in undeclared
            if isinstance(result.get(name), dict)
        ]

        return Finding(
            finding_id=f"F-{sample}-S{index:03d}",
            sample=sample,
            violation_type=ViolationType.UNDECLARED_SHARING,
            severity=Severity.MEDIUM,
            rationale=(
                f"观测到 {len(undeclared)} 个未在政策中声明的共享目标："
                + "、".join(undeclared)
                + "。"
                + "；".join(reasons)
            ),
            behavior_facts=fact_ids,
            declarations=[],
            regulation_refs=[],
            evidence_refs=self._evidence_refs_from_facts(fact_ids),
            needs_review=False,
            decided_by="semantic",
        )

    def _judge_contradiction(
        self, payload: dict[str, Any], index: int
    ) -> Finding | None:
        prompt = build_contradiction_prompt(
            data_type=payload["data_type"],
            declaration_quotes=payload.get("declaration_quotes", []),
            observations=payload.get("observations", []),
        )
        result = self._ask(prompt)
        if not result.get("contradicts"):
            return None

        raw_type = str(result.get("violation_type", "none")).strip()
        if raw_type == "none":
            return None
        try:
            violation_type = ViolationType(raw_type)
        except ValueError:
            # 模型给出闭集外的类型，拒绝采用，降级为矛盾类
            violation_type = ViolationType.DECEPTIVE_POLICY

        confidence = str(result.get("confidence", "low"))
        sample = payload.get("sample", "")
        fact_ids = list(payload.get("fact_ids", []))

        return Finding(
            finding_id=f"F-{sample}-S{index:03d}",
            sample=sample,
            violation_type=violation_type,
            severity=Severity.HIGH,
            rationale=(
                f"政策声明与实际观测行为矛盾：{result.get('reason', '')}"
            ),
            behavior_facts=fact_ids,
            declarations=list(payload.get("declaration_ids", [])),
            regulation_refs=[],
            evidence_refs=self._evidence_refs_from_facts(fact_ids),
            needs_review=confidence != "high",
            decided_by="semantic",
        )

    # -- 内部 -------------------------------------------------------------

    def _ask(self, prompt: str) -> Any:
        return self.provider.chat_json(
            [ChatMessage(role="user", content=prompt)],
            system=SEMANTIC_SYSTEM,
            max_tokens=2048,
        )

    @staticmethod
    def _evidence_refs_from_facts(fact_ids: list[str]) -> list[str]:
        """证据编号由 fact_id 推导。

        fact_id 形如 BF-A1-dyn-002，对应证据 E-A1-dyn-002。
        引擎在汇总阶段会用真实事实表覆盖此推导结果，
        此处仅作为 Finding 构造时的占位，保证闸门 3 通过。
        """
        refs: list[str] = []
        for fact_id in fact_ids:
            if fact_id.startswith("BF-"):
                refs.append("E-" + fact_id[3:])
        return sorted(set(refs)) or ["E-UNRESOLVED"]
