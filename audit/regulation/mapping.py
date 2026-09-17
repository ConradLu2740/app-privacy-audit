"""ViolationType → 法规标签 的映射表。

这是确定性代码，不经过 LLM。LLM 只负责判断「行为属于哪个违规类型」，
条号由本表 + RegulationLibrary 检索得出，因此条号不可能被模型编造。
"""

from __future__ import annotations

from audit.schema import ViolationType

#: 违规类型 → 条文标签集合（任一命中即检索到）
VIOLATION_TAGS: dict[ViolationType, list[str]] = {
    ViolationType.NO_PUBLIC_RULES: [
        "no_public_rules",
        "disclosure",
    ],
    ViolationType.NO_EXPLICIT_CONSENT: [
        "no_explicit_consent",
        "consent_required",
    ],
    ViolationType.COLLECT_BEFORE_CONSENT: [
        "collect_before_consent",
        "consent_required",
        "notification",
    ],
    ViolationType.BEYOND_SCOPE: [
        "beyond_scope",
        "minimal_necessity",
        "necessary_scope",
    ],
    ViolationType.UNDECLARED_SHARING: [
        "undeclared_sharing",
        "third_party_sharing",
        "notification",
    ],
    ViolationType.INSECURE_TRANSPORT: [
        "insecure_transport",
        "security_measures",
    ],
    ViolationType.DECEPTIVE_POLICY: [
        "deceptive_policy",
        "disclosure",
        "notification",
    ],
    ViolationType.NO_DELETION_CHANNEL: [
        "no_deletion_channel",
        "deletion_right",
    ],
}

#: 违规类型 → 中文名称，用于报告输出
VIOLATION_LABELS: dict[ViolationType, str] = {
    ViolationType.NO_PUBLIC_RULES: "未公开收集使用规则",
    ViolationType.NO_EXPLICIT_CONSENT: "未经同意收集使用个人信息",
    ViolationType.COLLECT_BEFORE_CONSENT: "同意前收集个人信息",
    ViolationType.BEYOND_SCOPE: "超范围或非必要收集",
    ViolationType.UNDECLARED_SHARING: "未声明的第三方共享",
    ViolationType.INSECURE_TRANSPORT: "明文或未加密传输",
    ViolationType.DECEPTIVE_POLICY: "隐私政策与实际行为不一致",
    ViolationType.NO_DELETION_CHANNEL: "未提供删除或注销渠道",
}

#: 数据类型 → 用于必要性判断的条文标签（可选，供 semantic.py 参考）
DATA_TYPE_TAGS: dict[str, list[str]] = {
    "location": ["necessary_scope"],
    "device_id": ["minimal_necessity"],
    "contacts": ["necessary_scope", "sensitive_info"],
    "sms": ["sensitive_info", "necessary_scope"],
    "installed_apps": ["minimal_necessity"],
    "clipboard": ["minimal_necessity"],
}


#: 应用类型关键词 → 《必要范围规定》中的类型标签
#: 用于让「超范围收集」判定引用到该应用类型对应的必要范围条文，
#: 而不是把十类应用的条文全部列出。
APP_CATEGORY_TAGS: dict[str, str] = {
    "地图导航": "category:map",
    "导航": "category:map",
    "即时通信": "category:im",
    "社交": "category:im",
    "新闻资讯": "category:news",
    "资讯": "category:news",
    "网上购物": "category:shopping",
    "电商": "category:shopping",
    "购物": "category:shopping",
    "餐饮外卖": "category:food",
    "外卖": "category:food",
    "实用工具": "category:tool",
    "工具": "category:tool",
    "天气": "category:tool",
    "日历": "category:tool",
    "网络社区": "category:social",
    "社区": "category:social",
    "论坛": "category:social",
    "在线影音": "category:video",
    "影音": "category:video",
    "视频": "category:video",
    "音乐": "category:video",
}


def category_tag_for(app_category: str | None) -> str | None:
    """把应用类型描述映射到类型标签；未命中返回 None。"""
    if not app_category:
        return None
    for keyword, tag in APP_CATEGORY_TAGS.items():
        if keyword in app_category:
            return tag
    return None


def tags_for_violation(violation_type: ViolationType | str) -> list[str]:
    if isinstance(violation_type, str):
        violation_type = ViolationType(violation_type)
    return VIOLATION_TAGS.get(violation_type, [])


def label_for_violation(violation_type: ViolationType | str) -> str:
    if isinstance(violation_type, str):
        violation_type = ViolationType(violation_type)
    return VIOLATION_LABELS.get(violation_type, violation_type.value)
