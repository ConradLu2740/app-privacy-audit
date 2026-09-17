"""对齐引擎 —— 编排规则、语义判定与法规检索。

见 docs/design/llm-compliance-engine.md 第 5.3 节。

编排顺序：
  1. 规则引擎跑确定性判定，产出 Finding[] 与语义候选 Candidate[]
  2. 语义判定处理候选，补充 Finding[]
  3. 为每条 Finding 检索法规条文（确定性，不经过 LLM）
  4. 过滤未核对条文（闸门 2）
  5. 用真实事实表修正 evidence_refs
"""

from __future__ import annotations

from dataclasses import dataclass, field

from audit.align.rules import RuleEngine
from audit.align.semantic import SemanticJudge
from audit.llm import LLMProvider
from audit.regulation import RegulationLibrary, label_for_violation
from audit.schema import (
    ArticleStatus,
    BehaviorFact,
    Declaration,
    Finding,
)


@dataclass
class AlignmentResult:
    findings: list[Finding] = field(default_factory=list)
    #: 因未核对而被剔除的条文引用：finding_id -> [article_id]
    filtered_unverified: dict[str, list[str]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    semantic_errors: list[str] = field(default_factory=list)

    def by_severity(self) -> dict[str, list[Finding]]:
        buckets: dict[str, list[Finding]] = {}
        for finding in self.findings:
            buckets.setdefault(finding.severity.value, []).append(finding)
        return buckets

    def to_dict(self) -> dict[str, object]:
        return {
            "findings": [f.to_dict() for f in self.findings],
            "filtered_unverified": self.filtered_unverified,
            "notes": self.notes,
            "semantic_errors": self.semantic_errors,
        }


class AlignmentEngine:
    """声明-行为对齐（DBA）引擎。"""

    def __init__(
        self,
        *,
        library: RegulationLibrary,
        provider: LLMProvider | None = None,
        app_category: str = "unknown",
        allow_unverified_articles: bool = False,
    ) -> None:
        self.library = library
        self.provider = provider
        self.app_category = app_category
        self.allow_unverified_articles = allow_unverified_articles

    def run(
        self,
        facts: list[BehaviorFact],
        declarations: list[Declaration],
        *,
        policy_text: str = "",
    ) -> AlignmentResult:
        engine = RuleEngine(
            app_category=self.app_category,
            semantic_available=self.provider is not None,
        )
        outcome = engine.run(facts, declarations, policy_text=policy_text)

        result = AlignmentResult(
            findings=list(outcome.findings),
            notes=list(outcome.notes),
        )

        # 语义判定
        if outcome.candidates:
            if self.provider is None:
                result.notes.append(
                    f"有 {len(outcome.candidates)} 项需要语义判定，但未配置 LLM provider，"
                    "已跳过。这些项在报告中应标为待核。"
                )
            else:
                judge = SemanticJudge(self.provider)
                for offset, candidate in enumerate(outcome.candidates, start=1):
                    finding = judge.judge(candidate, index=offset)
                    if finding is not None:
                        result.findings.append(finding)
                result.semantic_errors = judge.errors

        # 修正证据引用 + 检索法规条文
        fact_index = {f.fact_id: f for f in facts}
        for finding in result.findings:
            self._resolve_evidence(finding, fact_index)
            self._attach_regulations(finding, result)

        result.findings.sort(key=lambda f: (f.sample, f.finding_id))
        return result

    # -- 内部 -------------------------------------------------------------

    @staticmethod
    def _resolve_evidence(
        finding: Finding, fact_index: dict[str, BehaviorFact]
    ) -> None:
        """用真实事实表覆盖推导出的证据编号。"""
        refs = {
            fact_index[fact_id].evidence_ref
            for fact_id in finding.behavior_facts
            if fact_id in fact_index
        }
        if refs:
            finding.evidence_refs = sorted(refs)

    def _attach_regulations(self, finding: Finding, result: AlignmentResult) -> None:
        """按违规类型检索条文，取相关度最高的若干条。

        闸门 2：未核对条文默认剔除并记录。
        """
        articles = self.library.search_by_violation(
            finding.violation_type.value,
            include_unverified=True,
            app_category=self.app_category,
        )
        accepted: list[str] = []
        rejected: list[str] = []

        for article in articles:
            if article.status is ArticleStatus.VERIFIED or self.allow_unverified_articles:
                accepted.append(article.article_id)
            else:
                rejected.append(article.article_id)

        finding.regulation_refs = accepted
        if rejected:
            result.filtered_unverified[finding.finding_id] = rejected

    # -- 输出辅助 ---------------------------------------------------------

    @staticmethod
    def label(finding: Finding) -> str:
        return label_for_violation(finding.violation_type)
