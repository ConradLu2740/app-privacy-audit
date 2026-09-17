"""核心数据模型与枚举。

设计原则见 docs/design/llm-compliance-engine.md 第 3 节。

三条防幻觉闸门在本文件中以类型约束体现：
  1. Declaration.quote 必填 —— 抽取结果需通过原文子串校验（在 policy/extractor.py 校验）
  2. RegulationArticle.status —— 未核对条文默认不参与判定（在 align/engine.py 过滤）
  3. Finding.evidence_refs 非空 —— 在 Finding.__post_init__ 中强制校验
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


# --------------------------------------------------------------------------
# 枚举
# --------------------------------------------------------------------------


class FactSource(str, Enum):
    """行为事实来源，对应三线分析。"""

    STATIC = "static"
    DYNAMIC = "dynamic"
    TRAFFIC = "traffic"


class Confidence(str, Enum):
    """观测置信度。

    继承仓库既有认知纪律：静态命中只产生假设，不得单独定为违规。
    规则引擎要求 OBSERVED 才能产出高风险判定。
    """

    OBSERVED = "observed"  # 运行时真发生
    CODE_PATH_ONLY = "code_path_only"  # 仅代码路径存在


class ConsentPhase(str, Enum):
    """采集发生在用户同意隐私政策之前还是之后。"""

    BEFORE_CONSENT = "before_consent"
    AFTER_CONSENT = "after_consent"
    UNKNOWN = "unknown"


class Transport(str, Enum):
    HTTPS = "https"
    HTTP = "http"


class DataType(str, Enum):
    """归一化数据类别。

    静态分析、动态分析、流量分析、政策声明共用同一套取值，
    否则无法做集合差集。与 checklists/privacy-checklist.md 的 S/D/T 项对齐。
    """

    DEVICE_ID = "device_id"
    LOCATION = "location"
    CONTACTS = "contacts"
    SMS = "sms"
    CALL_LOG = "call_log"
    PHONE_STATE = "phone_state"
    INSTALLED_APPS = "installed_apps"
    CLIPBOARD = "clipboard"
    PHOTO_MEDIA = "photo_media"
    AUDIO_RECORD = "audio_record"
    CAMERA = "camera"
    SENSOR = "sensor"
    ACCOUNT = "account"
    STORAGE_FILES = "storage_files"


#: 通常被视为敏感、可用于必要性判断与风险定级的数据类别
SENSITIVE_DATA_TYPES: frozenset[DataType] = frozenset(
    {
        DataType.DEVICE_ID,
        DataType.LOCATION,
        DataType.CONTACTS,
        DataType.SMS,
        DataType.CALL_LOG,
        DataType.PHONE_STATE,
        DataType.INSTALLED_APPS,
        DataType.CLIPBOARD,
        DataType.PHOTO_MEDIA,
        DataType.AUDIO_RECORD,
        DataType.ACCOUNT,
    }
)


class DeclConfidence(str, Enum):
    """政策声明的确定性。

    ABSENT 用于表示政策中完全未出现该数据类别，
    这是「超范围收集」差集计算的依据。
    """

    EXPLICIT = "explicit"  # 政策明确声明
    INFERRED = "inferred"  # 需推理得出
    ABSENT = "absent"  # 政策未提及


class ViolationType(str, Enum):
    """违规类型闭集。

    对应《App 违法违规收集使用个人信息行为认定方法》六大类，
    另加传输与渠道两类。LLM 只能在此集合内选择，
    把开放生成问题转为闭集分类问题以保障准确率。
    """

    NO_PUBLIC_RULES = "no_public_rules"
    NO_EXPLICIT_CONSENT = "no_explicit_consent"
    COLLECT_BEFORE_CONSENT = "collect_before_consent"
    BEYOND_SCOPE = "beyond_scope"
    UNDECLARED_SHARING = "undeclared_sharing"
    INSECURE_TRANSPORT = "insecure_transport"
    DECEPTIVE_POLICY = "deceptive_policy"
    NO_DELETION_CHANNEL = "no_deletion_channel"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ArticleStatus(str, Enum):
    """法规条文核对状态。

    只有 VERIFIED 的条文默认可进入最终判定。
    """

    VERIFIED = "verified"
    UNVERIFIED = "unverified"


# --------------------------------------------------------------------------
# 实体
# --------------------------------------------------------------------------


class SchemaError(ValueError):
    """数据模型约束被违反。"""


@dataclass
class BehaviorFact:
    """统一行为事实 —— 三线分析的原子产出。"""

    fact_id: str
    sample: str
    source: FactSource
    evidence_ref: str
    data_type: DataType
    raw_observation: str
    actor: str = "app"
    phase: ConsentPhase = ConsentPhase.UNKNOWN
    destination: str | None = None
    transport: Transport | None = None
    confidence: Confidence = Confidence.OBSERVED
    observed_at: str | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_ref:
            raise SchemaError(f"{self.fact_id}: evidence_ref 不能为空")

    @property
    def is_sensitive(self) -> bool:
        return self.data_type in SENSITIVE_DATA_TYPES

    @property
    def is_observed(self) -> bool:
        return self.confidence is Confidence.OBSERVED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BehaviorFact":
        data = dict(raw)
        data["source"] = FactSource(data["source"])
        data["data_type"] = DataType(data["data_type"])
        data["phase"] = ConsentPhase(data.get("phase", "unknown"))
        data["confidence"] = Confidence(data.get("confidence", "observed"))
        transport = data.get("transport")
        data["transport"] = Transport(transport) if transport else None
        return cls(**data)


@dataclass
class Declaration:
    """隐私政策中的一条结构化声明。"""

    decl_id: str
    sample: str
    clause_id: str
    data_type: DataType
    purpose: str
    quote: str
    collect_phase: ConsentPhase = ConsentPhase.UNKNOWN
    shared_with: list[str] = field(default_factory=list)
    transport_protected: bool | None = None
    confidence: DeclConfidence = DeclConfidence.EXPLICIT
    source_url: str = ""

    def __post_init__(self) -> None:
        # 闸门 1：无原文引证的声明不得进入流水线。
        # ABSENT 是「政策未提及」的占位声明，天然没有原文，豁免。
        if self.confidence is not DeclConfidence.ABSENT and not self.quote.strip():
            raise SchemaError(f"{self.decl_id}: 非 ABSENT 声明必须携带原文引证 quote")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Declaration":
        data = dict(raw)
        data["data_type"] = DataType(data["data_type"])
        data["collect_phase"] = ConsentPhase(data.get("collect_phase", "unknown"))
        data["confidence"] = DeclConfidence(data.get("confidence", "explicit"))
        return cls(**data)


@dataclass
class RegulationArticle:
    """法规条文。"""

    article_id: str
    law: str
    article: str
    title: str
    text: str
    tags: list[str] = field(default_factory=list)
    status: ArticleStatus = ArticleStatus.UNVERIFIED
    verified_on: str | None = None
    source_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RegulationArticle":
        data = dict(raw)
        data["status"] = ArticleStatus(data.get("status", "unverified"))
        return cls(**data)


@dataclass
class Finding:
    """违规判定。"""

    finding_id: str
    sample: str
    violation_type: ViolationType
    severity: Severity
    rationale: str
    behavior_facts: list[str] = field(default_factory=list)
    declarations: list[str] = field(default_factory=list)
    regulation_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    needs_review: bool = False
    decided_by: str = "rule"  # rule | semantic

    def __post_init__(self) -> None:
        # 闸门 3：无证据不得出判定。
        if not self.evidence_refs:
            raise SchemaError(f"{self.finding_id}: evidence_refs 不能为空")
        if not self.behavior_facts:
            raise SchemaError(f"{self.finding_id}: behavior_facts 不能为空")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Finding":
        data = dict(raw)
        data["violation_type"] = ViolationType(data["violation_type"])
        data["severity"] = Severity(data["severity"])
        return cls(**data)


# --------------------------------------------------------------------------
# 批量序列化辅助
# --------------------------------------------------------------------------


def dump_all(items: list[Any]) -> list[dict[str, Any]]:
    return [item.to_dict() for item in items]
