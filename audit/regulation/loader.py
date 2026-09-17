"""法规条文库的加载与检索。

见 docs/design/llm-compliance-engine.md 第 5.2 节。

防幻觉闸门 2：未核对（status=unverified）的条文默认不参与判定。
"""

from __future__ import annotations

import json
from pathlib import Path

from audit.schema import ArticleStatus, RegulationArticle

DATA_DIR = Path(__file__).parent / "data"


class RegulationLibrary:
    """本地法规条文库。条文来自 JSON 文件，检索为确定性操作，不经过 LLM。"""

    def __init__(self, articles: list[RegulationArticle]) -> None:
        self._articles = articles
        self._by_id = {a.article_id: a for a in articles}

    # -- 构建 -------------------------------------------------------------

    @classmethod
    def load(cls, data_dir: str | Path | None = None) -> "RegulationLibrary":
        directory = Path(data_dir) if data_dir else DATA_DIR
        articles: list[RegulationArticle] = []

        for path in sorted(directory.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            meta = payload.get("_meta") or {}
            law = meta.get("law", path.stem)
            source_url = meta.get("source_url", "")
            for raw in payload.get("articles", []):
                data = dict(raw)
                data.setdefault("law", law)
                data.setdefault("source_url", source_url)
                data.setdefault("tags", [])
                articles.append(RegulationArticle.from_dict(data))

        if not articles:
            raise FileNotFoundError(f"{directory} 下未找到任何条文数据")
        return cls(articles)

    # -- 查询 -------------------------------------------------------------

    @property
    def articles(self) -> list[RegulationArticle]:
        return list(self._articles)

    def get(self, article_id: str) -> RegulationArticle:
        try:
            return self._by_id[article_id]
        except KeyError as exc:
            raise KeyError(f"条文库中不存在 {article_id}") from exc

    def verified_only(self) -> "RegulationLibrary":
        """返回仅含已核对条文的新库实例。"""
        return RegulationLibrary(
            [a for a in self._articles if a.status is ArticleStatus.VERIFIED]
        )

    def search(
        self,
        *,
        tags: list[str] | None = None,
        text_query: str | None = None,
        include_unverified: bool = True,
    ) -> list[RegulationArticle]:
        """按标签或文本检索。

        tags 为「任一命中」语义：传入的标签中有一个出现在条文 tags 里即命中。
        """
        results = self._articles
        if not include_unverified:
            results = [a for a in results if a.status is ArticleStatus.VERIFIED]

        if tags:
            wanted = set(tags)
            results = [a for a in results if wanted & set(a.tags)]

        if text_query:
            needle = text_query.strip()
            results = [
                a
                for a in results
                if needle in a.text or needle in a.title or needle in a.article
            ]

        return list(results)

    def search_by_violation(
        self,
        violation_type: str,
        *,
        include_unverified: bool = True,
        app_category: str | None = None,
        max_results: int = 4,
    ) -> list[RegulationArticle]:
        """按违规类型检索条文，按相关度排序后取前若干条。

        不做相关度排序的话，`consent_required` 这类通用标签会把十几条条文
        全部带出，报告里一次引用 11 个条号反而降低可信度。
        排序权重：标签在映射表中的位置越靠前越具体，权重越高；
        应用类型匹配的《必要范围规定》条文额外加权。
        """
        from audit.regulation.mapping import (
            category_tag_for,
            tags_for_violation,
        )

        wanted = tags_for_violation(violation_type)
        weight = {tag: len(wanted) - index for index, tag in enumerate(wanted)}
        category_tag = category_tag_for(app_category) if app_category else None

        scored: list[tuple[int, RegulationArticle]] = []
        for article in self._articles:
            if not include_unverified and article.status is not ArticleStatus.VERIFIED:
                continue
            score = sum(weight.get(tag, 0) for tag in article.tags)
            if score == 0:
                continue
            if category_tag and category_tag in article.tags:
                score += 3
            scored.append((score, article))

        scored.sort(key=lambda pair: (-pair[0], pair[1].article_id))
        return [article for _, article in scored[:max_results]]

    def stats(self) -> dict[str, int]:
        total = len(self._articles)
        verified = sum(
            1 for a in self._articles if a.status is ArticleStatus.VERIFIED
        )
        return {"total": total, "verified": verified, "unverified": total - verified}
