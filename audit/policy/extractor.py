"""隐私政策 → 结构化声明。

见 docs/design/llm-compliance-engine.md 第 5.1 节。

防幻觉闸门 1 的实现位置：
  LLM 返回的每条声明都要通过两道校验，不通过即丢弃并计数：
    - quote 必须是政策原文的子串
    - data_type 必须落在 DataType 闭集内
  丢弃率进评测报告，作为抽取质量的量化指标。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from audit.llm import ChatMessage, LLMProvider, LLMResponseError
from audit.policy.prompts import POLICY_SYSTEM, build_extraction_prompt
from audit.schema import DataType, DeclConfidence, Declaration, ConsentPhase

#: 条款切分用的编号模式
CLAUSE_PATTERNS = [
    re.compile(r"(?=^[一二三四五六七八九十]+、)", re.MULTILINE),
    re.compile(r"(?=^\d+[、.．]\s*)", re.MULTILINE),
    re.compile(r"(?=^第[一二三四五六七八九十百]+[条章])", re.MULTILINE),
]

#: 单段最大字符数，超过则按段落进一步切分
MAX_CLAUSE_CHARS = 4000


@dataclass
class ExtractionStats:
    """抽取质量统计，用于评测章节。"""

    clauses_total: int = 0
    clauses_processed: int = 0
    raw_declarations: int = 0
    accepted: int = 0
    dropped_bad_quote: int = 0
    dropped_bad_type: int = 0
    dropped_other: int = 0
    absent_placeholders: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def drop_rate(self) -> float:
        if not self.raw_declarations:
            return 0.0
        dropped = self.dropped_bad_quote + self.dropped_bad_type + self.dropped_other
        return dropped / self.raw_declarations

    def to_dict(self) -> dict[str, object]:
        return {
            "clauses_total": self.clauses_total,
            "clauses_processed": self.clauses_processed,
            "raw_declarations": self.raw_declarations,
            "accepted": self.accepted,
            "dropped_bad_quote": self.dropped_bad_quote,
            "dropped_bad_type": self.dropped_bad_type,
            "dropped_other": self.dropped_other,
            "absent_placeholders": self.absent_placeholders,
            "drop_rate": round(self.drop_rate, 4),
            "errors": self.errors,
        }


class PolicyExtractor:
    """把隐私政策文本抽取为 Declaration 列表。"""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def extract(
        self,
        policy_text: str,
        *,
        sample: str,
        source_url: str = "",
        add_absent_placeholders: bool = True,
    ) -> tuple[list[Declaration], ExtractionStats]:
        stats = ExtractionStats()
        clauses = split_clauses(policy_text)
        stats.clauses_total = len(clauses)

        declarations: list[Declaration] = []
        counter = 0

        for index, clause in enumerate(clauses, start=1):
            if len(clause.strip()) < 20:
                continue
            try:
                raw_items = self._extract_clause(clause, sample)
            except (LLMResponseError, Exception) as exc:  # noqa: BLE001
                stats.errors.append(f"clause {index}: {type(exc).__name__}: {exc}")
                continue

            stats.clauses_processed += 1
            for item in raw_items:
                stats.raw_declarations += 1
                declaration = self._validate(
                    item,
                    policy_text=policy_text,
                    sample=sample,
                    source_url=source_url,
                    counter=counter + 1,
                    stats=stats,
                )
                if declaration is not None:
                    counter += 1
                    declarations.append(declaration)

        stats.accepted = len(declarations)

        if add_absent_placeholders:
            placeholders = build_absent_placeholders(
                declarations, sample=sample, start_index=counter + 1
            )
            stats.absent_placeholders = len(placeholders)
            declarations.extend(placeholders)

        return declarations, stats

    # -- 内部 -------------------------------------------------------------

    def _extract_clause(self, clause: str, sample: str) -> list[dict]:
        prompt = build_extraction_prompt(clause, sample)
        payload = self.provider.chat_json(
            [ChatMessage(role="user", content=prompt)],
            system=POLICY_SYSTEM,
            max_tokens=4096,
        )
        if isinstance(payload, dict):
            items = payload.get("declarations", [])
        elif isinstance(payload, list):
            items = payload
        else:
            items = []
        return [item for item in items if isinstance(item, dict)]

    @staticmethod
    def _validate(
        item: dict,
        *,
        policy_text: str,
        sample: str,
        source_url: str,
        counter: int,
        stats: ExtractionStats,
    ) -> Declaration | None:
        # 闸门 1a：quote 必须是原文子串
        quote = str(item.get("quote", "")).strip()
        if not quote or not quote_in_text(quote, policy_text):
            stats.dropped_bad_quote += 1
            return None

        # 闸门 1b：data_type 必须在闭集内
        raw_type = str(item.get("data_type", "")).strip()
        try:
            data_type = DataType(raw_type)
        except ValueError:
            stats.dropped_bad_type += 1
            return None

        shared = item.get("shared_with") or []
        if isinstance(shared, str):
            shared = [shared]
        shared = [str(s).strip() for s in shared if str(s).strip()]

        transport = item.get("transport_protected")
        if transport is not None:
            transport = bool(transport)

        phase_raw = str(item.get("collect_phase", "unknown")).strip()
        try:
            phase = ConsentPhase(phase_raw)
        except ValueError:
            phase = ConsentPhase.UNKNOWN

        try:
            return Declaration(
                decl_id=f"D-{sample}-{counter:03d}",
                sample=sample,
                clause_id=f"C-{counter:03d}",
                data_type=data_type,
                purpose=str(item.get("purpose", "")).strip()[:120],
                quote=quote,
                collect_phase=phase,
                shared_with=shared,
                transport_protected=transport,
                confidence=DeclConfidence.EXPLICIT,
                source_url=source_url,
            )
        except Exception:  # noqa: BLE001
            stats.dropped_other += 1
            return None


# --------------------------------------------------------------------------
# 工具函数
# --------------------------------------------------------------------------


def normalize_for_match(text: str) -> str:
    """去掉空白与常见全半角差异，便于子串匹配。"""
    cleaned = re.sub(r"\s+", "", text)
    translation = str.maketrans(
        "０１２３４５６７８９（）：，。；、“”‘’", "0123456789():,.;,\"\"''"
    )
    return cleaned.translate(translation)


def quote_in_text(quote: str, policy_text: str) -> bool:
    """quote 是否出自政策原文。

    先做严格匹配，失败后做去空白匹配，容忍换行与空格差异。
    """
    if quote in policy_text:
        return True
    return normalize_for_match(quote) in normalize_for_match(policy_text)


def split_clauses(policy_text: str) -> list[str]:
    """按编号或段落切分政策文本。"""
    text = policy_text.strip()
    if not text:
        return []

    for pattern in CLAUSE_PATTERNS:
        parts = [p.strip() for p in pattern.split(text) if p.strip()]
        if len(parts) > 1:
            return _enforce_max_len(parts)

    # 无编号：按空行分段
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(parts) > 1:
        return _enforce_max_len(parts)

    return _enforce_max_len([text])


def _enforce_max_len(parts: list[str]) -> list[str]:
    """超长段落按长度再切，避免单次调用超出上下文。"""
    result: list[str] = []
    for part in parts:
        if len(part) <= MAX_CLAUSE_CHARS:
            result.append(part)
            continue
        for start in range(0, len(part), MAX_CLAUSE_CHARS):
            result.append(part[start : start + MAX_CLAUSE_CHARS])
    return result


def build_absent_placeholders(
    declarations: list[Declaration], *, sample: str, start_index: int
) -> list[Declaration]:
    """为政策中完全未出现的数据类别生成占位声明。

    这是「超范围收集」差集计算的基础：政策未提及某类数据，
    不等于不收集，而是意味着一旦观测到收集即构成未声明收集。
    """
    mentioned = {
        d.data_type for d in declarations if d.confidence is DeclConfidence.EXPLICIT
    }
    placeholders: list[Declaration] = []
    for offset, data_type in enumerate(DataType):
        if data_type in mentioned:
            continue
        index = start_index + offset
        placeholders.append(
            Declaration(
                decl_id=f"D-{sample}-{index:03d}",
                sample=sample,
                clause_id=f"C-absent-{data_type.value}",
                data_type=data_type,
                purpose="",
                quote="",
                confidence=DeclConfidence.ABSENT,
            )
        )
    return placeholders
