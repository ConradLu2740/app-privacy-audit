"""法规条文库。"""

from audit.regulation.loader import DATA_DIR, RegulationLibrary
from audit.regulation.mapping import (
    APP_CATEGORY_TAGS,
    DATA_TYPE_TAGS,
    VIOLATION_LABELS,
    VIOLATION_TAGS,
    category_tag_for,
    label_for_violation,
    tags_for_violation,
)

__all__ = [
    "APP_CATEGORY_TAGS",
    "DATA_DIR",
    "DATA_TYPE_TAGS",
    "VIOLATION_LABELS",
    "VIOLATION_TAGS",
    "RegulationLibrary",
    "category_tag_for",
    "label_for_violation",
    "tags_for_violation",
]
