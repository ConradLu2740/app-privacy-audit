"""政策抽取相关提示词模板。

提示词设计要点：
  1. 强制 JSON 输出，字段固定
  2. 强制 quote 原文引证 —— 抽取后由代码做子串校验，编造内容会被丢弃
  3. data_type 限定在闭集内，超集即丢弃
"""

from __future__ import annotations

from audit.schema import DataType

DATA_TYPE_LIST = "\n".join(f"  - {d.value}" for d in DataType)

POLICY_SYSTEM = """你是一个移动应用隐私政策结构化分析助手。
你的任务是从隐私政策文本中抽取结构化的数据收集声明。

严格遵守以下规则：
1. 只抽取文本中**明确写出**的内容，不要推断、不要补充常识、不要脑补。
2. 每条声明必须附带原文片段 quote，quote 必须逐字复制自给定文本。
3. data_type 只能从给定枚举中选择，无法归类时不要输出该条。
4. 文本中没有提到的内容，不要输出对应条目。

这是合规检测工具的一环，任何编造都会导致检测结论错误。"""


def build_extraction_prompt(policy_text: str, sample: str) -> str:
    return f"""样本标识：{sample}

请从下面的隐私政策文本中抽取所有关于个人信息收集的声明。

输出 JSON 对象，格式如下：
{{
  "declarations": [
    {{
      "data_type": "<枚举值>",
      "purpose": "<收集目的，简述，20 字以内>",
      "collect_phase": "before_consent | after_consent | unknown",
      "shared_with": ["<接收方名称，无则空数组>"],
      "transport_protected": true,
      "quote": "<逐字复制的原文片段>"
    }}
  ]
}}

data_type 可选值（必须完全匹配）：
{DATA_TYPE_LIST}

字段说明：
- collect_phase：该数据是在用户同意隐私政策前收集、还是之后。政策通常不写明，无法判断时填 unknown。
- transport_protected：政策是否声称该数据的传输受到加密保护。未提及填 null。
- quote：必须是从下方文本中逐字复制的片段，长度 10-200 字。

隐私政策文本：
---
{policy_text}
---

只输出 JSON，不要任何解释文字。"""


# --------------------------------------------------------------------------
# 语义判定提示词
# --------------------------------------------------------------------------

SEMANTIC_SYSTEM = """你是一个移动应用隐私合规研判助手，为合规检测工具提供语义判断。

严格遵守以下规则：
1. 只依据给定的事实做判断，不要引入外部假设。
2. 不确定时倾向于保守判断，并在 reason 中说明不确定的原因。
3. violation_type 只能从给定枚举中选择。
4. 输出必须是合法 JSON。"""


def build_necessity_prompt(
    *,
    data_type: str,
    app_category: str,
    declared_purposes: list[str],
    observations: list[str],
) -> str:
    purposes = "；".join(declared_purposes) if declared_purposes else "（政策未声明该数据的收集目的）"
    obs = "\n".join(f"  - {o}" for o in observations)
    return f"""判断以下数据收集行为是否属于「超范围或非必要收集」。

数据类别：{data_type}
应用类型：{app_category}
政策声明的收集目的：{purposes}

观测到的行为：
{obs}

判断标准：
- 若该数据类别与应用的基本功能服务直接相关，且政策已声明该目的，则不属于超范围。
- 若该数据类别与应用基本功能无关，或政策未声明而实际收集，则属于超范围。
- 若政策未声明但该数据确为实现基本功能所必需（例如导航类应用的位置信息），
  则属于「政策披露不足」而非「超范围收集」，请在 reason 中区分。

输出 JSON：
{{
  "is_beyond_scope": true,
  "is_necessary_for_core_function": true,
  "reason": "<判断理由，60 字以内>",
  "confidence": "high | medium | low"
}}

只输出 JSON。"""


def build_sharing_prompt(
    *,
    observed_targets: list[str],
    declared_shared_with: list[str],
    policy_quotes: list[str],
) -> str:
    targets = "\n".join(f"  - {t}" for t in observed_targets)
    declared = "；".join(declared_shared_with) if declared_shared_with else "（政策未列出任何第三方）"
    quotes = "\n".join(f"  > {q}" for q in policy_quotes) if policy_quotes else "（无）"
    return f"""判断以下第三方共享目标是否已在隐私政策中声明。

观测到的共享目标（SDK 包名或域名）：
{targets}

政策中列出的接收方：
{declared}

政策相关原文：
{quotes}

判断标准：
- 政策中出现该目标的名称、其所属公司名称、或其业务描述，视为已声明。
- 政策仅笼统写「合作伙伴」「关联方」而未点名具体主体，视为披露不足。
- 政策完全未提及该目标，视为未声明。

输出 JSON 对象，键为观测目标名称：
{{
  "<目标名称>": {{
    "declared": true,
    "matched_text": "<政策中对应的表述，未声明则为空>",
    "reason": "<判断理由，40 字以内>"
  }}
}}

只输出 JSON。"""


def build_contradiction_prompt(
    *,
    data_type: str,
    declaration_quotes: list[str],
    observations: list[str],
) -> str:
    quotes = "\n".join(f"  > {q}" for q in declaration_quotes) if declaration_quotes else "（政策未提及该数据类别）"
    obs = "\n".join(f"  - {o}" for o in observations)
    return f"""判断政策声明与实际观测行为之间是否存在矛盾。

数据类别：{data_type}

政策声明原文：
{quotes}

实际观测行为：
{obs}

判断标准：
- 政策声称「不收集」「仅本地处理」「不上传」而观测到收集或上传 → 矛盾。
- 政策声称传输加密而观测到明文传输 → 矛盾。
- 政策未提及该数据类别但观测到收集 → 这属于「未声明收集」，不算政策自相矛盾。
- 政策描述模糊但未作出否定性承诺 → 不算矛盾。

输出 JSON：
{{
  "contradicts": true,
  "violation_type": "deceptive_policy | beyond_scope | insecure_transport | none",
  "reason": "<判断理由，60 字以内>",
  "confidence": "high | medium | low"
}}

只输出 JSON。"""
