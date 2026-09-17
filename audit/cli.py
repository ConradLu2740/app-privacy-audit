"""命令行入口。

用法见 docs/design/llm-compliance-engine.md 第 7 节。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from audit.align import AlignmentEngine
from audit.llm import LLMError, build_provider, load_config
from audit.policy import PolicyExtractor
from audit.regulation import RegulationLibrary
from audit.report import ReportGenerator
from audit.schema import BehaviorFact, Declaration


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _print_usage(provider) -> None:
    """打印本次运行的 token 消耗，便于控制成本。"""
    usage = getattr(provider, "usage", None)
    if usage is None or usage.total_tokens == 0:
        return
    print(
        f"  模型 {provider.model}（{provider.name}）："
        f"输入 {usage.prompt_tokens} / 输出 {usage.completion_tokens} tokens"
    )


def _load_facts(path: str | Path) -> list[BehaviorFact]:
    raw = _read_json(path)
    items = raw.get("facts", raw) if isinstance(raw, dict) else raw
    return [BehaviorFact.from_dict(item) for item in items]


def _load_declarations(path: str | Path) -> list[Declaration]:
    raw = _read_json(path)
    items = raw.get("declarations", raw) if isinstance(raw, dict) else raw
    return [Declaration.from_dict(item) for item in items]


# --------------------------------------------------------------------------
# 子命令
# --------------------------------------------------------------------------


def cmd_policy_extract(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    provider = build_provider(config, provider=args.provider, model=args.model)
    policy_text = Path(args.policy).read_text(encoding="utf-8")

    extractor = PolicyExtractor(provider)
    declarations, stats = extractor.extract(
        policy_text, sample=args.sample, source_url=args.source_url or ""
    )

    _write_json(
        args.out,
        {
            "sample": args.sample,
            "source_url": args.source_url or "",
            "provider": provider.name,
            "model": provider.model,
            "stats": stats.to_dict(),
            "declarations": [d.to_dict() for d in declarations],
        },
    )

    print(f"样本 {args.sample}：抽取完成")
    print(f"  条款 {stats.clauses_total} 段，处理 {stats.clauses_processed} 段")
    print(
        f"  LLM 返回 {stats.raw_declarations} 条，通过校验 {stats.accepted} 条，"
        f"丢弃率 {stats.drop_rate:.2%}"
    )
    print(f"  政策未声明类别占位 {stats.absent_placeholders} 条")
    if stats.errors:
        print(f"  处理中发生 {len(stats.errors)} 个错误（详见输出文件）")
    _print_usage(provider)
    print(f"  已写入 {args.out}")
    return 0


def cmd_align(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    library = RegulationLibrary.load(args.regulation_dir)

    provider = None
    if args.provider != "none":
        try:
            provider = build_provider(config, provider=args.provider, model=args.model)
        except (LLMError, ValueError) as exc:
            print(f"警告：LLM provider 不可用（{exc}），仅执行确定性规则。", file=sys.stderr)

    facts = _load_facts(args.facts)
    declarations = _load_declarations(args.declarations)
    policy_text = (
        Path(args.policy).read_text(encoding="utf-8") if args.policy else ""
    )

    engine = AlignmentEngine(
        library=library,
        provider=provider,
        app_category=args.app_category,
        allow_unverified_articles=args.allow_unverified,
    )
    result = engine.run(facts, declarations, policy_text=policy_text)

    _write_json(args.out, result.to_dict())

    print(f"输入 {len(facts)} 条行为事实、{len(declarations)} 条政策声明")
    print(f"产出 {len(result.findings)} 条违规判定")
    for finding in result.findings:
        review = "（待核）" if finding.needs_review else ""
        regs = "、".join(finding.regulation_refs) or "无已核对条文"
        print(
            f"  {finding.finding_id}  {finding.violation_type.value}  "
            f"{finding.severity.value}  {regs}{review}"
        )
    if result.filtered_unverified:
        print(
            f"  {len(result.filtered_unverified)} 条判定因条文未核对而暂无法规引用"
            "（核对后自动生效）"
        )
    for note in result.notes:
        print(f"  说明：{note}")
    if provider is not None:
        _print_usage(provider)
    print(f"  已写入 {args.out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    library = RegulationLibrary.load(args.regulation_dir)
    raw = _read_json(args.findings)
    from audit.align import AlignmentResult
    from audit.schema import Finding

    result = AlignmentResult(
        findings=[Finding.from_dict(f) for f in raw.get("findings", [])],
        filtered_unverified=raw.get("filtered_unverified", {}),
        notes=raw.get("notes", []),
        semantic_errors=raw.get("semantic_errors", []),
    )

    facts = _load_facts(args.facts) if args.facts else []
    declarations = _load_declarations(args.declarations) if args.declarations else []
    stats = _read_json(args.stats) if args.stats else None

    generator = ReportGenerator(library)
    markdown = generator.render(
        result,
        facts=facts,
        declarations=declarations,
        extraction_stats=stats.get("stats") if isinstance(stats, dict) else None,
    )

    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    print(f"报告已写入 {args.out}（{len(markdown)} 字符）")
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    """端到端冒烟：使用 FakeProvider，无需网络与 API key。"""
    from audit.llm import FakeProvider

    base = Path(__file__).resolve().parent.parent
    fixture_dir = base / "fixtures"

    facts = _load_facts(fixture_dir / "facts_a3.json")
    policy_text = (fixture_dir / "policy_a3.txt").read_text(encoding="utf-8")

    provider = FakeProvider(response_file=fixture_dir / "fake_responses.json")
    extractor = PolicyExtractor(provider)
    declarations, stats = extractor.extract(
        policy_text, sample="A3", source_url="https://newpipe.net/legal/privacy/"
    )

    library = RegulationLibrary.load()
    engine = AlignmentEngine(
        library=library, provider=provider, app_category="在线影音类"
    )
    result = engine.run(facts, declarations, policy_text=policy_text)

    generator = ReportGenerator(library)
    markdown = generator.render(
        result,
        facts=facts,
        declarations=declarations,
        extraction_stats=stats.to_dict(),
    )

    out_dir = base / "out"
    _write_json(
        out_dir / "D-A3.json",
        {
            "sample": "A3",
            "source_url": "https://newpipe.net/legal/privacy/",
            "provider": provider.name,
            "model": provider.model,
            "stats": stats.to_dict(),
            "declarations": [d.to_dict() for d in declarations],
        },
    )
    _write_json(out_dir / "F-A3.json", result.to_dict())
    (out_dir / "05-compliance-review.md").write_text(markdown, encoding="utf-8")

    print("冒烟测试通过（FakeProvider，无网络调用）")
    print(f"  政策声明 {len(declarations)} 条，抽取丢弃率 {stats.drop_rate:.2%}")
    print(f"  违规判定 {len(result.findings)} 条")
    print(f"  条文库 {library.stats()}")
    print(f"  产物已写入 {out_dir}")
    return 0


# --------------------------------------------------------------------------
# 参数解析
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    # 公共选项同时挂在主解析器与子命令上，因此 `--provider none align ...`
    # 与 `align ... --provider none` 两种写法都可用。
    common = argparse.ArgumentParser(add_help=False)
    # default=SUPPRESS：子解析器不设置未传入的选项，避免用默认值覆盖主解析器已解析的值。
    common.add_argument(
        "--config", default=argparse.SUPPRESS, help="配置文件路径，默认查找 ./config.yaml"
    )
    common.add_argument(
        "--provider",
        default=argparse.SUPPRESS,
        help="LLM 提供方：proma-cloud / openai-compatible / fake / none",
    )
    common.add_argument(
        "--model", default=argparse.SUPPRESS, help="模型 ID，覆盖配置文件"
    )
    common.add_argument(
        "--regulation-dir",
        default=argparse.SUPPRESS,
        help="法规条文数据目录，默认 audit/regulation/data",
    )

    parser = argparse.ArgumentParser(
        prog="audit",
        description="APP 隐私合规检测流水线（LLM 合规研判引擎）",
        parents=[common],
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser(
        "policy-extract", help="从隐私政策抽取结构化声明", parents=[common]
    )
    p_extract.add_argument("--policy", required=True, help="政策文本文件")
    p_extract.add_argument("--sample", required=True, help="样本标识，如 A3")
    p_extract.add_argument("--source-url", help="政策来源 URL")
    p_extract.add_argument("--out", required=True, help="输出 JSON 路径")
    p_extract.set_defaults(func=cmd_policy_extract)

    p_align = sub.add_parser(
        "align", help="对齐行为事实与政策声明，产出违规判定", parents=[common]
    )
    p_align.add_argument("--facts", required=True, help="行为事实 JSON")
    p_align.add_argument("--declarations", required=True, help="政策声明 JSON")
    p_align.add_argument("--policy", help="政策原文，用于渠道类规则检查")
    p_align.add_argument("--app-category", default="unknown", help="应用类型，用于必要性判断")
    p_align.add_argument("--out", required=True, help="输出 JSON 路径")
    p_align.add_argument(
        "--allow-unverified",
        action="store_true",
        help="允许引用未核对条文（默认禁止，用于自查）",
    )
    p_align.set_defaults(func=cmd_align)

    p_report = sub.add_parser(
        "report", help="从判定结果生成报告章节", parents=[common]
    )
    p_report.add_argument("--findings", required=True, help="判定结果 JSON")
    p_report.add_argument("--facts", help="行为事实 JSON，用于生成事实表")
    p_report.add_argument("--declarations", help="政策声明 JSON，用于生成声明表")
    p_report.add_argument("--stats", help="抽取统计 JSON")
    p_report.add_argument("--out", required=True, help="输出 Markdown 路径")
    p_report.set_defaults(func=cmd_report)

    p_smoke = sub.add_parser(
        "smoke", help="端到端冒烟（FakeProvider，无需网络）", parents=[common]
    )
    p_smoke.set_defaults(func=cmd_smoke)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # common 选项用 SUPPRESS 默认值，未传入时属性不存在，这里补齐
    for name, fallback in (
        ("config", None),
        ("provider", None),
        ("model", None),
        ("regulation_dir", None),
    ):
        if not hasattr(args, name):
            setattr(args, name, fallback)
    try:
        return args.func(args)
    except (LLMError, ValueError, FileNotFoundError, KeyError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
