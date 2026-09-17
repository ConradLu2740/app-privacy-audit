"""端到端冒烟测试。

用 FakeProvider 跑通「政策抽取 → 对齐研判 → 报告生成」全链路，
不需要网络与 API key。专家核查源码时可直接运行验证。

运行：python -m pytest tests/ -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from audit.align import AlignmentEngine, RuleEngine
from audit.llm import FakeProvider
from audit.policy import PolicyExtractor, quote_in_text, split_clauses
from audit.regulation import RegulationLibrary
from audit.report import ReportGenerator
from audit.schema import (
    BehaviorFact,
    ConsentPhase,
    DataType,
    DeclConfidence,
    Declaration,
    FactSource,
    Finding,
    SchemaError,
    Severity,
    Transport,
    ViolationType,
)

BASE = Path(__file__).resolve().parent.parent
FIXTURES = BASE / "fixtures"


@pytest.fixture
def library() -> RegulationLibrary:
    return RegulationLibrary.load()


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider(response_file=FIXTURES / "fake_responses.json")


@pytest.fixture
def facts() -> list[BehaviorFact]:
    raw = json.loads((FIXTURES / "facts_a3.json").read_text(encoding="utf-8"))
    return [BehaviorFact.from_dict(item) for item in raw["facts"]]


@pytest.fixture
def policy_text() -> str:
    return (FIXTURES / "policy_a3.txt").read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# 闸门 1：原文引证
# --------------------------------------------------------------------------


def test_quote_must_come_from_policy() -> None:
    policy = "我们不会收集您的通讯录。"
    assert quote_in_text("我们不会收集您的通讯录", policy)
    assert not quote_in_text("我们收集您的通讯录", policy)


def test_quote_tolerates_whitespace_and_fullwidth() -> None:
    policy = "我们不会收集您的通讯录、短信内容。"
    assert quote_in_text("我们不会收集您的通讯录、短信内容", policy)


def test_declaration_requires_quote() -> None:
    with pytest.raises(SchemaError):
        Declaration(
            decl_id="D-X-001",
            sample="X",
            clause_id="C-001",
            data_type=DataType.LOCATION,
            purpose="测试",
            quote="",
        )


def test_absent_declaration_exempt_from_quote() -> None:
    decl = Declaration(
        decl_id="D-X-002",
        sample="X",
        clause_id="C-absent-location",
        data_type=DataType.LOCATION,
        purpose="",
        quote="",
        confidence=DeclConfidence.ABSENT,
    )
    assert decl.confidence is DeclConfidence.ABSENT


def test_extractor_drops_fabricated_quote(policy_text: str) -> None:
    """LLM 编造的原文引证必须被丢弃。"""

    class LyingProvider(FakeProvider):
        def chat(self, messages, **kwargs):  # type: ignore[override]
            return json.dumps(
                {
                    "declarations": [
                        {
                            "data_type": "location",
                            "purpose": "编造",
                            "quote": "这段文字在政策原文中根本不存在",
                        }
                    ]
                },
                ensure_ascii=False,
            )

    extractor = PolicyExtractor(LyingProvider())
    declarations, stats = extractor.extract(policy_text, sample="T")
    assert stats.dropped_bad_quote == stats.clauses_processed
    assert not [d for d in declarations if d.confidence is DeclConfidence.EXPLICIT]


def test_extractor_drops_out_of_enum_type(policy_text: str) -> None:
    class BadTypeProvider(FakeProvider):
        def chat(self, messages, **kwargs):  # type: ignore[override]
            return json.dumps(
                {
                    "declarations": [
                        {
                            "data_type": "brainwave",
                            "purpose": "越界类型",
                            "quote": "会收集您的位置信息用于展示本地天气",
                        }
                    ]
                },
                ensure_ascii=False,
            )

    extractor = PolicyExtractor(BadTypeProvider())
    _, stats = extractor.extract(policy_text, sample="T")
    assert stats.dropped_bad_type == stats.clauses_processed


# --------------------------------------------------------------------------
# 闸门 2：法规条文核对状态
# --------------------------------------------------------------------------


def test_unverified_articles_are_filtered(library: RegulationLibrary) -> None:
    """未核对条文默认不得进入判定。"""
    engine = AlignmentEngine(library=library, provider=None, app_category="在线影音类")
    fact = BehaviorFact(
        fact_id="BF-T-dyn-001",
        sample="T",
        source=FactSource.DYNAMIC,
        evidence_ref="E-T-dyn-01",
        data_type=DataType.DEVICE_ID,
        raw_observation="getDeviceId 在同意前调用",
        phase=ConsentPhase.BEFORE_CONSENT,
    )
    result = engine.run([fact], [])
    finding = next(
        f for f in result.findings if f.violation_type is ViolationType.COLLECT_BEFORE_CONSENT
    )
    assert finding.regulation_refs == []
    assert finding.finding_id in result.filtered_unverified


def test_allow_unverified_articles(library: RegulationLibrary) -> None:
    engine = AlignmentEngine(
        library=library,
        provider=None,
        app_category="在线影音类",
        allow_unverified_articles=True,
    )
    fact = BehaviorFact(
        fact_id="BF-T-dyn-001",
        sample="T",
        source=FactSource.DYNAMIC,
        evidence_ref="E-T-dyn-01",
        data_type=DataType.DEVICE_ID,
        raw_observation="getDeviceId 在同意前调用",
        phase=ConsentPhase.BEFORE_CONSENT,
    )
    result = engine.run([fact], [])
    finding = next(
        f for f in result.findings if f.violation_type is ViolationType.COLLECT_BEFORE_CONSENT
    )
    assert finding.regulation_refs
    assert result.filtered_unverified == {}


def test_verified_library_is_empty_at_seed_state(library: RegulationLibrary) -> None:
    """种子数据的 status 全为 unverified，这是刻意的默认值。"""
    stats = library.stats()
    assert stats["verified"] == 0
    assert library.verified_only().articles == []


# --------------------------------------------------------------------------
# 闸门 3：无证据不得出判定
# --------------------------------------------------------------------------


def test_finding_requires_evidence() -> None:
    with pytest.raises(SchemaError):
        Finding(
            finding_id="F-T-001",
            sample="T",
            violation_type=ViolationType.BEYOND_SCOPE,
            severity=Severity.MEDIUM,
            rationale="无证据的判定",
            behavior_facts=["BF-T-001"],
            evidence_refs=[],
        )


def test_fact_requires_evidence_ref() -> None:
    with pytest.raises(SchemaError):
        BehaviorFact(
            fact_id="BF-T-001",
            sample="T",
            source=FactSource.STATIC,
            evidence_ref="",
            data_type=DataType.LOCATION,
            raw_observation="x",
        )


# --------------------------------------------------------------------------
# 规则引擎
# --------------------------------------------------------------------------


def test_static_only_hit_is_downgraded() -> None:
    """仅代码路径命中的同意前采集，应降级并标记待核。"""
    from audit.schema import Confidence

    engine = RuleEngine(semantic_available=False)
    fact = BehaviorFact(
        fact_id="BF-T-sta-001",
        sample="T",
        source=FactSource.STATIC,
        evidence_ref="E-T-sta-01",
        data_type=DataType.DEVICE_ID,
        raw_observation="getDeviceId 调用点存在",
        phase=ConsentPhase.BEFORE_CONSENT,
        confidence=Confidence.CODE_PATH_ONLY,
    )
    outcome = engine.run([fact], [])
    finding = outcome.findings[0]
    assert finding.severity is Severity.LOW
    assert finding.needs_review is True


def test_insecure_transport_detected() -> None:
    engine = RuleEngine()
    fact = BehaviorFact(
        fact_id="BF-T-trf-001",
        sample="T",
        source=FactSource.TRAFFIC,
        evidence_ref="E-T-trf-01",
        data_type=DataType.LOCATION,
        raw_observation="位置以明文 HTTP 提交",
        transport=Transport.HTTP,
        destination="api.example.com",
    )
    outcome = engine.run([fact], [])
    types = {f.violation_type for f in outcome.findings}
    assert ViolationType.INSECURE_TRANSPORT in types


def test_https_transport_not_flagged() -> None:
    engine = RuleEngine()
    fact = BehaviorFact(
        fact_id="BF-T-trf-001",
        sample="T",
        source=FactSource.TRAFFIC,
        evidence_ref="E-T-trf-01",
        data_type=DataType.LOCATION,
        raw_observation="位置经 HTTPS 提交",
        transport=Transport.HTTPS,
        destination="api.example.com",
    )
    outcome = engine.run([fact], [])
    types = {f.violation_type for f in outcome.findings}
    assert ViolationType.INSECURE_TRANSPORT not in types


def test_beyond_scope_skipped_when_semantic_available() -> None:
    """有 LLM 时超范围判定交给语义环节，避免重复报告。"""
    engine = RuleEngine(semantic_available=True)
    fact = BehaviorFact(
        fact_id="BF-T-dyn-001",
        sample="T",
        source=FactSource.DYNAMIC,
        evidence_ref="E-T-dyn-01",
        data_type=DataType.CLIPBOARD,
        raw_observation="读取剪贴板",
    )
    outcome = engine.run([fact], [])
    assert not [f for f in outcome.findings if f.violation_type is ViolationType.BEYOND_SCOPE]
    assert [c for c in outcome.candidates if c.kind == "necessity"]


def test_declared_type_not_flagged_beyond_scope() -> None:
    engine = RuleEngine(semantic_available=False)
    fact = BehaviorFact(
        fact_id="BF-T-dyn-001",
        sample="T",
        source=FactSource.DYNAMIC,
        evidence_ref="E-T-dyn-01",
        data_type=DataType.LOCATION,
        raw_observation="读取位置",
    )
    declaration = Declaration(
        decl_id="D-T-001",
        sample="T",
        clause_id="C-001",
        data_type=DataType.LOCATION,
        purpose="展示本地天气",
        quote="收集您的位置信息",
    )
    outcome = engine.run([fact], [declaration])
    assert not [f for f in outcome.findings if f.violation_type is ViolationType.BEYOND_SCOPE]


def test_missing_deletion_channel_detected() -> None:
    engine = RuleEngine()
    declaration = Declaration(
        decl_id="D-T-001",
        sample="T",
        clause_id="C-001",
        data_type=DataType.ACCOUNT,
        purpose="账号",
        quote="我们收集您的手机号",
    )
    outcome = engine.run([], [declaration], policy_text="本政策仅说明信息收集范围。")
    types = {f.violation_type for f in outcome.findings}
    assert ViolationType.NO_DELETION_CHANNEL in types


def test_deletion_channel_present_not_flagged() -> None:
    engine = RuleEngine()
    declaration = Declaration(
        decl_id="D-T-001",
        sample="T",
        clause_id="C-001",
        data_type=DataType.ACCOUNT,
        purpose="账号",
        quote="我们收集您的手机号",
    )
    outcome = engine.run(
        [], [declaration], policy_text="您可以随时删除个人数据或注销账号。"
    )
    types = {f.violation_type for f in outcome.findings}
    assert ViolationType.NO_DELETION_CHANNEL not in types


# --------------------------------------------------------------------------
# 政策切分
# --------------------------------------------------------------------------


def test_split_clauses_by_chinese_numbering() -> None:
    text = "一、信息收集\n我们收集位置信息。\n二、信息存储\n我们加密存储。"
    clauses = split_clauses(text)
    assert len(clauses) == 2
    assert clauses[0].startswith("一、")


# --------------------------------------------------------------------------
# 端到端
# --------------------------------------------------------------------------


def test_end_to_end_pipeline(
    library: RegulationLibrary,
    provider: FakeProvider,
    facts: list[BehaviorFact],
    policy_text: str,
) -> None:
    """政策抽取 → 对齐研判 → 报告生成，全程不触网。"""
    extractor = PolicyExtractor(provider)
    declarations, stats = extractor.extract(policy_text, sample="A3")
    assert stats.accepted > 0

    engine = AlignmentEngine(
        library=library, provider=provider, app_category="在线影音类"
    )
    result = engine.run(facts, declarations, policy_text=policy_text)
    assert result.findings

    types = {f.violation_type for f in result.findings}
    assert ViolationType.COLLECT_BEFORE_CONSENT in types
    assert ViolationType.INSECURE_TRANSPORT in types

    # 每条判定都必须携带证据
    for finding in result.findings:
        assert finding.evidence_refs
        assert finding.behavior_facts

    markdown = ReportGenerator(library).render(
        result, facts=facts, declarations=declarations, extraction_stats=stats.to_dict()
    )
    assert "违规总表" in markdown
    assert "法规核对记录" in markdown
    assert "F-A3-001" in markdown


def test_no_llm_still_produces_rule_findings(
    library: RegulationLibrary, facts: list[BehaviorFact]
) -> None:
    """未配置 LLM 时，确定性规则仍应产出判定。"""
    engine = AlignmentEngine(library=library, provider=None, app_category="在线影音类")
    result = engine.run(facts, [], policy_text="")
    types = {f.violation_type for f in result.findings}
    assert ViolationType.COLLECT_BEFORE_CONSENT in types
    assert ViolationType.INSECURE_TRANSPORT in types
    assert result.notes
