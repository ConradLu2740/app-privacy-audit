"""确定性规则引擎。

见 docs/design/llm-compliance-engine.md 第 2.1 节与 5.3 节。

本模块**不调用 LLM**。所有判定都是集合运算或时序比较，因此可写单元测试、
结果 100% 可复现。语义模糊的部分（必要性、共享对象匹配、政策矛盾）
交给 semantic.py。

继承仓库既有认知纪律：
  - 静态命中（confidence=code_path_only）只能产出「待核项」，不能定为高风险违规
  - 判定必须携带证据编号，无证据不得产出
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from audit.schema import (
    BehaviorFact,
    Confidence,
    ConsentPhase,
    DeclConfidence,
    Declaration,
    Finding,
    Severity,
    Transport,
    ViolationType,
)

#: 各违规类型的默认严重级别
DEFAULT_SEVERITY: dict[ViolationType, Severity] = {
    ViolationType.COLLECT_BEFORE_CONSENT: Severity.HIGH,
    ViolationType.INSECURE_TRANSPORT: Severity.HIGH,
    ViolationType.DECEPTIVE_POLICY: Severity.HIGH,
    ViolationType.BEYOND_SCOPE: Severity.MEDIUM,
    ViolationType.UNDECLARED_SHARING: Severity.MEDIUM,
    ViolationType.NO_EXPLICIT_CONSENT: Severity.MEDIUM,
    ViolationType.NO_DELETION_CHANNEL: Severity.LOW,
    ViolationType.NO_PUBLIC_RULES: Severity.LOW,
}

#: 仅代码路径命中时，降级后的级别
DOWNGRADED: dict[Severity, Severity] = {
    Severity.HIGH: Severity.LOW,
    Severity.MEDIUM: Severity.LOW,
    Severity.LOW: Severity.INFO,
    Severity.INFO: Severity.INFO,
}


@dataclass
class Candidate:
    """待 LLM 语义判定的候选。规则已确定它「需要判断」，但判断依据不足。"""

    kind: str  # necessity | sharing | contradiction
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleOutcome:
    findings: list[Finding] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    #: 规则无法判定但值得记录的情况（如政策缺章节）
    notes: list[str] = field(default_factory=list)


class RuleEngine:
    """规则引擎。输入行为事实与政策声明，输出确定性判定与语义候选。

    semantic_available 为 True 时，「超范围收集」只产出候选而不直接下判定——
    是否属于「非必要」需要语义判断，由 SemanticJudge 落定，避免同一问题被重复报告。
    为 False 时（未配置 LLM）则产出降级的兜底判定，标记待核。
    """

    def __init__(
        self, *, app_category: str = "unknown", semantic_available: bool = False
    ) -> None:
        self.app_category = app_category
        self.semantic_available = semantic_available

    def run(
        self,
        facts: list[BehaviorFact],
        declarations: list[Declaration],
        *,
        policy_text: str = "",
    ) -> RuleOutcome:
        outcome = RuleOutcome()

        self._rule_before_consent(facts, outcome)
        self._rule_insecure_transport(facts, outcome)
        self._rule_beyond_scope(facts, declarations, outcome)
        self._rule_undeclared_sharing(facts, declarations, outcome)
        self._rule_contradiction_candidates(facts, declarations, outcome)
        self._rule_policy_channels(facts, declarations, policy_text, outcome)

        return outcome

    # -- 规则实现 ---------------------------------------------------------

    def _rule_before_consent(
        self, facts: list[BehaviorFact], outcome: RuleOutcome
    ) -> None:
        """同意前收集：时序比较，纯确定性。"""
        hits = [
            f
            for f in facts
            if f.phase is ConsentPhase.BEFORE_CONSENT and f.is_sensitive
        ]
        if not hits:
            return

        observed = [f for f in hits if f.is_observed]
        severity = DEFAULT_SEVERITY[ViolationType.COLLECT_BEFORE_CONSENT]
        if not observed:
            severity = DOWNGRADED[severity]

        outcome.findings.append(
            self._make_finding(
                sample=hits[0].sample,
                violation_type=ViolationType.COLLECT_BEFORE_CONSENT,
                severity=severity,
                facts=hits,
                rationale=(
                    f"在用户同意隐私政策前观测到 {len(hits)} 项敏感数据采集行为："
                    + "、".join(sorted({f.data_type.value for f in hits}))
                    + "。"
                    + (
                        "证据来自运行时观测。"
                        if observed
                        else "仅有代码路径证据，需运行时复核。"
                    )
                ),
                decided_by="rule",
                needs_review=not observed,
                index=len(outcome.findings) + 1,
            )
        )

    def _rule_insecure_transport(
        self, facts: list[BehaviorFact], outcome: RuleOutcome
    ) -> None:
        """明文传输：传输协议字段比较，纯确定性。"""
        hits = [
            f
            for f in facts
            if f.transport is Transport.HTTP and f.is_sensitive and f.is_observed
        ]
        if not hits:
            return

        outcome.findings.append(
            self._make_finding(
                sample=hits[0].sample,
                violation_type=ViolationType.INSECURE_TRANSPORT,
                severity=Severity.HIGH,
                facts=hits,
                rationale=(
                    "观测到敏感数据经明文 HTTP 传输："
                    + "、".join(
                        sorted(
                            f"{f.data_type.value} → {f.destination or '未知目标'}"
                            for f in hits
                        )
                    )
                    + "。"
                ),
                decided_by="rule",
                index=len(outcome.findings) + 1,
            )
        )

    def _rule_beyond_scope(
        self,
        facts: list[BehaviorFact],
        declarations: list[Declaration],
        outcome: RuleOutcome,
    ) -> None:
        """超范围收集：集合差集。

        差集给出「哪些数据类别被收集但政策未声明」，
        至于是否属于「非必要」需要语义判断，故同时产出候选。
        """
        declared_types = {
            d.data_type for d in declarations if d.confidence is DeclConfidence.EXPLICIT
        }
        observed_types: dict[Any, list[BehaviorFact]] = {}
        for fact in facts:
            if fact.is_sensitive:
                observed_types.setdefault(fact.data_type, []).append(fact)

        for data_type, group in sorted(
            observed_types.items(), key=lambda kv: kv[0].value
        ):
            if data_type in declared_types:
                continue

            observed = [f for f in group if f.is_observed]

            # 有 LLM 时交给语义判定落定，避免与 semantic finding 重复
            if not self.semantic_available:
                severity = DEFAULT_SEVERITY[ViolationType.BEYOND_SCOPE]
                if not observed:
                    severity = DOWNGRADED[severity]

                outcome.findings.append(
                    self._make_finding(
                        sample=group[0].sample,
                        violation_type=ViolationType.BEYOND_SCOPE,
                        severity=severity,
                        facts=group,
                        rationale=(
                            f"观测到 {data_type.value} 的采集，但隐私政策未声明该数据类别"
                            f"（共 {len(group)} 项证据）。未配置 LLM，未能判断是否属非必要，"
                            "需人工复核。"
                        ),
                        decided_by="rule",
                        needs_review=True,
                        index=len(outcome.findings) + 1,
                    )
                )

            outcome.candidates.append(
                Candidate(
                    kind="necessity",
                    payload={
                        "data_type": data_type.value,
                        "app_category": self.app_category,
                        "declared_purposes": [],
                        "observations": [
                            f.raw_observation for f in group[:5]
                        ],
                        "fact_ids": [f.fact_id for f in group],
                        "sample": group[0].sample,
                    },
                )
            )

    def _rule_undeclared_sharing(
        self,
        facts: list[BehaviorFact],
        declarations: list[Declaration],
        outcome: RuleOutcome,
    ) -> None:
        """未声明共享：观测目标集合 − 政策声明集合。"""
        declared_targets = {
            s.strip().lower()
            for d in declarations
            for s in d.shared_with
            if s.strip()
        }
        policy_quotes = [d.quote for d in declarations if d.shared_with and d.quote]

        # 共享目标来源：流量目标域名 + 归因到 SDK 的行为
        targets: dict[str, list[BehaviorFact]] = {}
        for fact in facts:
            if fact.destination:
                targets.setdefault(fact.destination, []).append(fact)
            if fact.actor.startswith("sdk:"):
                targets.setdefault(fact.actor, []).append(fact)

        unmatched = {
            name: group
            for name, group in targets.items()
            if not self._matches_declared(name, declared_targets)
        }
        if not unmatched:
            return

        outcome.candidates.append(
            Candidate(
                kind="sharing",
                payload={
                    "observed_targets": sorted(unmatched),
                    "declared_shared_with": sorted(declared_targets),
                    "policy_quotes": policy_quotes[:10],
                    "target_facts": {
                        name: [f.fact_id for f in group]
                        for name, group in unmatched.items()
                    },
                    "sample": facts[0].sample if facts else "",
                },
            )
        )

    def _rule_contradiction_candidates(
        self,
        facts: list[BehaviorFact],
        declarations: list[Declaration],
        outcome: RuleOutcome,
    ) -> None:
        """政策矛盾：为「政策有否定性表述但观测到收集」的情况产出候选。"""
        negation_markers = (
            "不收集",
            "不会收集",
            "不获取",
            "仅本地",
            "不上传",
            "不会上传",
            "不存储",
            "不会存储",
            "不共享",
            "不会共享",
        )

        for declaration in declarations:
            if declaration.confidence is DeclConfidence.ABSENT:
                continue
            if not any(marker in declaration.quote for marker in negation_markers):
                continue

            related = [
                f
                for f in facts
                if f.data_type is declaration.data_type and f.is_observed
            ]
            if not related:
                continue

            outcome.candidates.append(
                Candidate(
                    kind="contradiction",
                    payload={
                        "data_type": declaration.data_type.value,
                        "declaration_quotes": [declaration.quote],
                        "declaration_ids": [declaration.decl_id],
                        "observations": [f.raw_observation for f in related[:5]],
                        "fact_ids": [f.fact_id for f in related],
                        "sample": declaration.sample,
                    },
                )
            )

    def _rule_policy_channels(
        self,
        facts: list[BehaviorFact],
        declarations: list[Declaration],
        policy_text: str,
        outcome: RuleOutcome,
    ) -> None:
        """删除/注销渠道与规则公开：对政策文本做关键词检查。

        这类缺陷的证据就是政策文本本身，因此合成一条静态事实作为证据载体。
        """
        sample = declarations[0].sample if declarations else (
            facts[0].sample if facts else ""
        )
        if not sample or not policy_text:
            return

        deletion_keywords = ("删除", "注销", "撤回", "更正")
        if not any(k in policy_text for k in deletion_keywords):
            synthetic = BehaviorFact(
                fact_id=f"BF-{sample}-pol-001",
                sample=sample,
                source=facts[0].source if facts else _default_source(),
                evidence_ref=f"E-{sample}-pol-01",
                data_type=declarations[0].data_type if declarations else _default_type(),
                raw_observation="隐私政策文本中未出现删除、注销、撤回或更正相关条款",
                actor="policy-document",
                confidence=Confidence.OBSERVED,
                note="政策文本层面的缺陷，证据为政策原文本身",
            )
            outcome.findings.append(
                self._make_finding(
                    sample=sample,
                    violation_type=ViolationType.NO_DELETION_CHANNEL,
                    severity=DEFAULT_SEVERITY[ViolationType.NO_DELETION_CHANNEL],
                    facts=[synthetic],
                    rationale=(
                        "政策文本中未检索到删除、注销、撤回同意或更正相关条款，"
                        "可能未向用户提供行使权利的渠道。"
                    ),
                    decided_by="rule",
                    needs_review=True,
                    index=len(outcome.findings) + 1,
                )
            )

    # -- 工具 -------------------------------------------------------------

    @staticmethod
    def _matches_declared(target: str, declared: set[str]) -> bool:
        """目标名是否已被政策声明覆盖（子串双向匹配，容忍包名与公司名差异）。"""
        lowered = target.lower()
        for item in declared:
            if not item:
                continue
            if item in lowered or lowered in item:
                return True
        return False

    @staticmethod
    def _make_finding(
        *,
        sample: str,
        violation_type: ViolationType,
        severity: Severity,
        facts: list[BehaviorFact],
        rationale: str,
        index: int,
        decided_by: str,
        needs_review: bool = False,
    ) -> Finding:
        return Finding(
            finding_id=f"F-{sample}-{index:03d}",
            sample=sample,
            violation_type=violation_type,
            severity=severity,
            rationale=rationale,
            behavior_facts=[f.fact_id for f in facts],
            declarations=[],
            regulation_refs=[],
            evidence_refs=sorted({f.evidence_ref for f in facts}),
            needs_review=needs_review,
            decided_by=decided_by,
        )


def _default_source():
    from audit.schema import FactSource

    return FactSource.STATIC


def _default_type():
    from audit.schema import DataType

    return DataType.ACCOUNT
