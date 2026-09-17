#!/usr/bin/env python3
"""LLM 合规研判引擎评测集（eval set）运行器。

每个评测用例（evals/cases/<case>/）包含：
  policy.txt           隐私政策文本
  facts.json           行为事实（BF-*，三线统一格式）
  fake_responses.json  离线模式：FakeProvider 的按键匹配响应
  expected.json        标准答案：期望判定 + 闸门断言

评分维度：(violation_type, data_type) 对上的 precision / recall / F1，
以及抽取闸门的计数断言（如幻觉引证必须被丢弃）。

用法：
  # 离线模式（默认，无需网络与 API key，结果确定可复现）
  python evals/run_eval.py

  # 实测模式（用真实 LLM 跑抽取与语义判定，验证引擎对真实模型的稳健性）
  set AUDIT_LLM_API_KEY=... && set AUDIT_LLM_MODEL=...
  python evals/run_eval.py --live

退出码：0 = 全部用例通过；1 = 存在失败用例（可作回归测试挂 CI）。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from audit.align import AlignmentEngine  # noqa: E402
from audit.llm import FakeProvider, LLMProvider  # noqa: E402
from audit.policy import PolicyExtractor  # noqa: E402
from audit.regulation import RegulationLibrary  # noqa: E402
from audit.schema import BehaviorFact  # noqa: E402

CASES_DIR = Path(__file__).resolve().parent / "cases"


@dataclass
class CaseResult:
    case: str
    description: str = ""
    expected: set[tuple[str, str]] = field(default_factory=set)
    actual: set[tuple[str, str]] = field(default_factory=set)
    gate_failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    extraction: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.actual == self.expected and not self.gate_failures

    def metrics(self) -> tuple[float, float, float]:
        tp = len(self.expected & self.actual)
        fp = len(self.actual - self.expected)
        fn = len(self.expected - self.actual)
        precision = tp / (tp + fp) if tp + fp else 1.0
        recall = tp / (tp + fn) if tp + fn else 1.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 1.0
        return precision, recall, f1


def load_case(case_dir: Path) -> dict:
    return {
        "policy": (case_dir / "policy.txt").read_text(encoding="utf-8"),
        "facts": [
            BehaviorFact.from_dict(raw)
            for raw in json.loads((case_dir / "facts.json").read_text(encoding="utf-8"))["facts"]
        ],
        "expected": json.loads((case_dir / "expected.json").read_text(encoding="utf-8")),
    }


def make_provider(case_dir: Path, live: bool) -> LLMProvider:
    if live:
        # 走与 CLI 一致的构建路径：config.yaml / AUDIT_LLM_* 环境变量
        from audit.llm import build_provider, load_config

        return build_provider(load_config())
    return FakeProvider(response_file=case_dir / "fake_responses.json")


def run_case(case_dir: Path, library: RegulationLibrary, live: bool) -> CaseResult:
    data = load_case(case_dir)
    expected_cfg = data["expected"]
    sample = expected_cfg.get("case", case_dir.name).upper().replace("-", "")
    app_category = expected_cfg.get("app_category", "unknown")

    provider = make_provider(case_dir, live)
    extractor = PolicyExtractor(provider)
    declarations, stats = extractor.extract(
        data["policy"], sample=sample, add_absent_placeholders=True
    )

    engine = AlignmentEngine(
        library=library,
        provider=provider,
        app_category=app_category,
        allow_unverified_articles=False,
    )
    result = engine.run(data["facts"], declarations, policy_text=data["policy"])

    fact_index = {f.fact_id: f for f in data["facts"]}
    actual: set[tuple[str, str]] = set()
    for finding in result.findings:
        for fid in finding.behavior_facts:
            fact = fact_index.get(fid)
            if fact is not None:
                actual.add((finding.violation_type.value, fact.data_type.value))

    expected = {
        (item["violation_type"], item["data_type"])
        for item in expected_cfg.get("expect_findings", [])
    }

    res = CaseResult(
        case=case_dir.name,
        description=expected_cfg.get("description", ""),
        expected=expected,
        actual=actual,
        notes=list(result.notes),
        extraction={
            "clauses_total": stats.clauses_total,
            "clauses_processed": stats.clauses_processed,
            "raw_declarations": stats.raw_declarations,
            "accepted": stats.accepted,
            "dropped_bad_quote": stats.dropped_bad_quote,
            "dropped_bad_type": stats.dropped_bad_type,
            "dropped_other": stats.dropped_other,
            "absent_placeholders": stats.absent_placeholders,
            "semantic_errors": len(result.semantic_errors),
        },
    )

    gates = expected_cfg.get("gates", {})
    if "min_raw_declarations" in gates:
        if stats.raw_declarations < gates["min_raw_declarations"]:
            res.gate_failures.append(
                f"raw_declarations {stats.raw_declarations} < 期望下限 {gates['min_raw_declarations']}"
            )
    if "expect_dropped_bad_quote" in gates:
        if stats.dropped_bad_quote != gates["expect_dropped_bad_quote"]:
            res.gate_failures.append(
                f"dropped_bad_quote {stats.dropped_bad_quote} != 期望 {gates['expect_dropped_bad_quote']}"
            )
    if "max_accepted_declarations" in gates:
        if stats.accepted > gates["max_accepted_declarations"]:
            res.gate_failures.append(
                f"accepted {stats.accepted} > 期望上限 {gates['max_accepted_declarations']}"
            )
    return res


def render_report(results: list[CaseResult], live: bool) -> str:
    mode = "live（真实 LLM）" if live else "offline（FakeProvider，确定性）"
    lines = [
        "# LLM 合规研判引擎评测报告",
        "",
        f"- 运行模式：{mode}",
        f"- 用例数：{len(results)}，通过：{sum(1 for r in results if r.passed)}",
        "",
        "| 用例 | 判定 P | R | F1 | 期望 | 实际 | 抽取(原始/接受/丢引证) | 结果 |",
        "|------|-------|---|---|------|------|------------------------|------|",
    ]
    for r in results:
        p, rec, f1 = r.metrics()
        exp = ", ".join(f"{t}/{d}" for t, d in sorted(r.expected)) or "∅"
        act = ", ".join(f"{t}/{d}" for t, d in sorted(r.actual)) or "∅"
        mark = "✅" if r.passed else "❌"
        lines.append(
            f"| {r.case} | {p:.2f} | {rec:.2f} | {f1:.2f} | {exp} | {act} "
            f"| {r.extraction.get('raw_declarations', 0)}/"
            f"{r.extraction.get('accepted', 0)}/"
            f"{r.extraction.get('dropped_bad_quote', 0)} | {mark} |"
        )
    lines.append("")
    for r in results:
        if r.passed:
            continue
        lines += [f"## ❌ {r.case}", "", f"> {r.description}", "", "**差异：**"]
        for item in sorted(r.expected - r.actual):
            lines.append(f"- 漏报：{item[0]} / {item[1]}")
        for item in sorted(r.actual - r.expected):
            lines.append(f"- 误报：{item[0]} / {item[1]}")
        for failure in r.gate_failures:
            lines.append(f"- 闸门断言失败：{failure}")
        if r.notes:
            lines.append("- 引擎备注：" + "；".join(r.notes))
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--live", action="store_true",
                    help="用真实 LLM（AUDIT_LLM_* 环境变量）替代 FakeProvider")
    ap.add_argument("--report", type=Path, default=BASE / "out" / "eval_report.md",
                    help="报告输出路径（默认 out/eval_report.md）")
    args = ap.parse_args(argv)

    library = RegulationLibrary.load()
    case_dirs = sorted(p for p in CASES_DIR.iterdir() if p.is_dir())
    if not case_dirs:
        print(f"no cases under {CASES_DIR}", file=sys.stderr)
        return 2

    results = [run_case(d, library, args.live) for d in case_dirs]
    report = render_report(results, args.live)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nreport -> {args.report}")
    failed = [r.case for r in results if not r.passed]
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("ALL CASES PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
