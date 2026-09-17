"""检测报告章节生成。

见 docs/design/llm-compliance-engine.md 第 5.5 节。

生成 docs/report/05-compliance-review.md 的对应内容，
替代人工逐条填写三列对照表。
"""

from __future__ import annotations

from datetime import date

from audit.align.engine import AlignmentResult
from audit.regulation import RegulationLibrary, label_for_violation
from audit.schema import (
    BehaviorFact,
    Declaration,
    DeclConfidence,
    Finding,
    Severity,
)

SEVERITY_LABEL = {
    Severity.HIGH: "高",
    Severity.MEDIUM: "中",
    Severity.LOW: "低",
    Severity.INFO: "信息",
}

DECIDED_LABEL = {"rule": "规则引擎", "semantic": "LLM 语义判定"}


class ReportGenerator:
    """从判定结果生成 Markdown 报告章节。"""

    def __init__(self, library: RegulationLibrary) -> None:
        self.library = library

    def render(
        self,
        result: AlignmentResult,
        *,
        samples: list[str] | None = None,
        facts: list[BehaviorFact] | None = None,
        declarations: list[Declaration] | None = None,
        extraction_stats: dict | None = None,
        generated_on: str | None = None,
    ) -> str:
        facts = facts or []
        declarations = declarations or []
        sample_list = samples or sorted({f.sample for f in result.findings})
        today = generated_on or date.today().isoformat()

        lines: list[str] = []
        lines.append("# 05 · 合规对照（自动生成）")
        lines.append("")
        lines.append(
            "> 本文件由 `audit report` 从结构化判定结果生成。"
            "生成后需人工复核，尤其是标记为「待核」的条目。"
        )
        lines.append(f"> 生成日期：{today}｜引擎版本：audit 0.1.0")
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.extend(self._summary_table(result))
        lines.extend(self._stats_section(result, extraction_stats, declarations))

        for sample in sample_list:
            lines.extend(
                self._sample_section(
                    sample,
                    [f for f in result.findings if f.sample == sample],
                    facts=[f for f in facts if f.sample == sample],
                    declarations=[d for d in declarations if d.sample == sample],
                )
            )

        lines.extend(self._regulation_record())
        lines.extend(self._limitations(result))
        return "\n".join(lines).rstrip() + "\n"

    # -- 各章节 -----------------------------------------------------------

    def _summary_table(self, result: AlignmentResult) -> list[str]:
        lines = ["## 1. 违规总表", ""]
        if not result.findings:
            lines.append("本次分析未产出任何违规判定。")
            lines.append("")
            return lines

        lines.append("| 判定 ID | 样本 | 违规类型 | 级别 | 法规条文 | 证据编号 | 判定方式 | 待核 |")
        lines.append("|---------|------|----------|------|----------|----------|----------|------|")
        for finding in result.findings:
            regulations = "、".join(finding.regulation_refs) or "—（见说明）"
            evidence = "、".join(finding.evidence_refs)
            lines.append(
                f"| {finding.finding_id} | {finding.sample} | "
                f"{label_for_violation(finding.violation_type)} | "
                f"{SEVERITY_LABEL[finding.severity]} | {regulations} | {evidence} | "
                f"{DECIDED_LABEL.get(finding.decided_by, finding.decided_by)} | "
                f"{'是' if finding.needs_review else '否'} |"
            )
        lines.append("")

        counts: dict[str, int] = {}
        for finding in result.findings:
            key = label_for_violation(finding.violation_type)
            counts[key] = counts.get(key, 0) + 1
        lines.append("按类型统计：" + "；".join(f"{k} {v} 项" for k, v in sorted(counts.items())))
        lines.append("")
        return lines

    def _stats_section(
        self,
        result: AlignmentResult,
        extraction_stats: dict | None,
        declarations: list[Declaration],
    ) -> list[str]:
        lines = ["## 2. 流水线指标", ""]

        if extraction_stats:
            lines.append("### 2.1 政策抽取质量")
            lines.append("")
            lines.append("| 指标 | 数值 |")
            lines.append("|------|------|")
            lines.append(f"| 条款总数 | {extraction_stats.get('clauses_total', 0)} |")
            lines.append(
                f"| 已处理条款 | {extraction_stats.get('clauses_processed', 0)} |"
            )
            lines.append(
                f"| LLM 返回声明数 | {extraction_stats.get('raw_declarations', 0)} |"
            )
            lines.append(f"| 通过校验 | {extraction_stats.get('accepted', 0)} |")
            lines.append(
                f"| 因原文引证校验失败被丢弃 | {extraction_stats.get('dropped_bad_quote', 0)} |"
            )
            lines.append(
                f"| 因数据类别越界被丢弃 | {extraction_stats.get('dropped_bad_type', 0)} |"
            )
            lines.append(
                f"| 丢弃率 | {extraction_stats.get('drop_rate', 0.0):.2%} |"
            )
            lines.append("")
            lines.append(
                "丢弃率反映 LLM 抽取的可靠性：被丢弃的条目均未通过"
                "「原文引证必须是政策原文子串」或「数据类别必须在闭集内」的校验，"
                "因此不可能把编造内容带进判定。"
            )
            lines.append("")

        absent = [d for d in declarations if d.confidence is DeclConfidence.ABSENT]
        if absent:
            lines.append("### 2.2 政策未声明的数据类别")
            lines.append("")
            lines.append(
                "以下数据类别在政策文本中完全未出现，一旦观测到收集即构成未声明收集："
            )
            lines.append("")
            lines.append("　" + "、".join(d.data_type.value for d in absent))
            lines.append("")

        if result.filtered_unverified:
            lines.append("### 2.3 因未核对而被剔除的条文引用")
            lines.append("")
            lines.append(
                "以下条文引用未通过「引用前核对原文」的闸门，已从判定中剔除。"
                "核对官方原文并在 `audit/regulation/data/*.json` 中将 `status` 改为 "
                "`verified`、填写 `verified_on` 后即可生效："
            )
            lines.append("")
            for finding_id, article_ids in sorted(result.filtered_unverified.items()):
                lines.append(f"- {finding_id}：{'、'.join(article_ids)}")
            lines.append("")

        return lines

    def _sample_section(
        self,
        sample: str,
        findings: list[Finding],
        *,
        facts: list[BehaviorFact],
        declarations: list[Declaration],
    ) -> list[str]:
        lines = [f"## 3. 样本 {sample}", ""]

        if facts:
            lines.append("### 3.1 行为事实")
            lines.append("")
            lines.append("| 事实 ID | 来源 | 数据类别 | 观测点 | 阶段 | 目标 | 传输 | 置信度 | 证据 |")
            lines.append("|---------|------|----------|--------|------|------|------|--------|------|")
            for fact in facts:
                lines.append(
                    f"| {fact.fact_id} | {fact.source.value} | {fact.data_type.value} | "
                    f"{fact.raw_observation} | {fact.phase.value} | "
                    f"{fact.destination or '—'} | "
                    f"{fact.transport.value if fact.transport else '—'} | "
                    f"{'运行时观测' if fact.is_observed else '仅代码路径'} | "
                    f"{fact.evidence_ref} |"
                )
            lines.append("")

        if declarations:
            explicit = [d for d in declarations if d.confidence is DeclConfidence.EXPLICIT]
            if explicit:
                lines.append("### 3.2 政策声明")
                lines.append("")
                lines.append("| 声明 ID | 数据类别 | 收集目的 | 共享对象 | 原文引证 |")
                lines.append("|---------|----------|----------|----------|----------|")
                for decl in explicit:
                    quote = decl.quote.replace("|", "\\|")[:80]
                    shared = "、".join(decl.shared_with) or "—"
                    lines.append(
                        f"| {decl.decl_id} | {decl.data_type.value} | "
                        f"{decl.purpose or '—'} | {shared} | {quote}… |"
                    )
                lines.append("")

        lines.append("### 3.3 逐条判定")
        lines.append("")
        if not findings:
            lines.append("本样本未产出违规判定。")
            lines.append("")
            return lines

        for finding in findings:
            review = "　**（待人工复核）**" if finding.needs_review else ""
            lines.append(
                f"#### {finding.finding_id}　{label_for_violation(finding.violation_type)}"
                f"（{SEVERITY_LABEL[finding.severity]}）{review}"
            )
            lines.append("")
            lines.append(f"- 判定方式：{DECIDED_LABEL.get(finding.decided_by, finding.decided_by)}")
            lines.append(f"- 行为事实：{'、'.join(finding.behavior_facts)}")
            if finding.declarations:
                lines.append(f"- 关联声明：{'、'.join(finding.declarations)}")
            lines.append(
                f"- 法规条文：{'、'.join(finding.regulation_refs) or '未检索到已核对条文'}"
            )
            lines.append(f"- 证据编号：{'、'.join(finding.evidence_refs)}")
            lines.append(f"- 判定理由：{finding.rationale}")
            lines.append("")
        return lines

    def _regulation_record(self) -> list[str]:
        lines = ["## 4. 法规核对记录", ""]
        stats = self.library.stats()
        lines.append(
            f"条文库共 {stats['total']} 条，其中已核对 {stats['verified']} 条、"
            f"未核对 {stats['unverified']} 条。未核对条文默认不参与判定。"
        )
        lines.append("")
        lines.append("| 条文 ID | 法规 | 条款 | 核对状态 | 核对日期 |")
        lines.append("|---------|------|------|----------|----------|")
        for article in sorted(self.library.articles, key=lambda a: a.article_id):
            status = "已核对" if article.status.value == "verified" else "**未核对**"
            lines.append(
                f"| {article.article_id} | {article.law} | {article.article} | "
                f"{status} | {article.verified_on or '—'} |"
            )
        lines.append("")
        return lines

    def _limitations(self, result: AlignmentResult) -> list[str]:
        lines = ["## 5. 本方法的局限", ""]
        lines.append(
            "- 判定依赖输入的行为事实完整性。静态线只产出假设，"
            "缺少动态或流量证据时，相关判定会被降级并标记待核。"
        )
        lines.append(
            "- LLM 语义判定存在波动，所有 `decided_by=semantic` 的条目都需人工复核。"
        )
        lines.append(
            "- 法规条文须核对官方原文后方可引用。未核对条文在流水线中被自动剔除，"
            "不会出现在最终结论里。"
        )
        lines.append(
            "- 「未观测到」不等于「不存在」。观测窗口、样本版本与设备环境都会影响结果。"
        )
        if result.notes:
            lines.append("")
            lines.append("本次运行的补充说明：")
            lines.append("")
            for note in result.notes:
                lines.append(f"- {note}")
        if result.semantic_errors:
            lines.append("")
            lines.append("语义判定过程中的错误：")
            lines.append("")
            for error in result.semantic_errors:
                lines.append(f"- {error}")
        lines.append("")
        return lines
