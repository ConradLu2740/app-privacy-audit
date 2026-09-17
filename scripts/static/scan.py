#!/usr/bin/env python3
"""Static keyword scanner for Jadx-decompiled Android sources.

Scans a Jadx-exported `sources/` tree for sensitive API / SDK fingerprints,
groups hits by category aligned to the privacy checklist (S-* items), and
emits a Markdown report with file counts and sample paths only — no source
excerpts, so the output is safe to commit under evidence/<pkg>/static/.

Usage:
    python scripts/static/scan.py <jadx-sources-dir> [-o report.md] [--top N]

Example:
    python scripts/static/scan.py %USERPROFILE%\\privacy-lab\\jadx-moji\\sources ^
        -o evidence/com.moji.mjweather/static/E-A1-sta-02.md

Exit codes: 0 = scan completed (even with 0 hits), 2 = bad input dir.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Keyword table. Aligned to checklists/privacy-checklist.md S-* items.
# Keys are lowercase; matching is case-insensitive on file text.
# Keep entries as API names / distinctive identifiers, not generic words.
# ---------------------------------------------------------------------------
CATEGORIES: dict[str, dict[str, list[str]]] = {
    "S-10 设备标识": {
        "keywords": [
            "getdeviceid", "getimei", "getmeid", "getsubscriberid",
            "getsimserialnumber", "getandroidid", "android_id",
            "getmacaddress", "getserial", "build.serial",
            "oaid", "umeng", "umid", "deviceid",
        ],
        "note": "IMEI/IMSI/MAC/OAID 等设备标识线索（静态命中 ≠ 运行时调用）",
    },
    "S-12 定位": {
        "keywords": [
            "getlastknownlocation", "requestlocationupdates",
            "fusedlocationprovider", "locationmanager",
            "geofence", "getlatitude", "getlongitude",
        ],
        "note": "定位 API 调用点",
    },
    "S-13 通讯录": {
        "keywords": [
            "contactscontract", "read_contacts", "phonelookup",
        ],
        "note": "通讯录读取",
    },
    "S-14 剪贴板": {
        "keywords": [
            "clipboardmanager", "getprimaryclip", "setprimaryclip",
            "addprimaryclipchangelistener", "onprimaryclipchanged",
        ],
        "note": "剪贴板读写/监听",
    },
    "S-15 应用列表": {
        "keywords": [
            "getinstalledpackages", "getinstalledapplications",
            "query_all_packages", "launcherapps", "usagestatsmanager",
        ],
        "note": "已安装应用枚举（含 QUERY_ALL_PACKAGES 相关路径）",
    },
    "S-20 存储/文件": {
        "keywords": [
            "getexternalstoragedirectory", "getexternalfilesdir",
            "mode_world_readable", "mode_world_writeable",
            "openfileoutput",
        ],
        "note": "外部存储与危险文件模式",
    },
    "S-21 网络安全": {
        "keywords": [
            "http://", "addjavascriptinterface", "setjavascriptenabled",
            "cleartexttraffic", "networksecurityconfig", "trustmanager",
            "hostnameverifier", "sslsocketsfactory",
        ],
        "note": "明文 HTTP / WebView 注入面 / 证书校验自定义",
    },
    "S-22 三方 SDK 指纹": {
        "keywords": [
            "umeng", "alipay", "mtop", "alibaba", "taobao",
            "tencent", "qqconnect", "wechat", "wxapi",
            "jpush", "getui", "geyt", "gdt", "bugly",
            "amap", "gaode", "baidumap", "baidu.location",
            "toutiao", "pangle", "穿山甲", "kuaishou", "kwai",
            "sentry", "firebase", "appsflyer", "adjust",
        ],
        "note": "第三方 SDK 包名/类名指纹，用于共享清单交叉核对",
    },
}

SOURCE_SUFFIXES = {".java", ".kt", ".smali"}
DEFAULT_TOP = 10


@dataclass
class CategoryResult:
    name: str
    note: str
    total_hits: int = 0
    files: set[str] = field(default_factory=set)
    keywords_hit: set[str] = field(default_factory=set)


def scan_tree(root: Path) -> tuple[list[CategoryResult], int]:
    # 单一合并正则，每个文件只扫一遍；关键字必须包含字母数字或 _，
    # 避免短词误匹配。
    all_keywords: dict[str, str] = {}
    for cat, spec in CATEGORIES.items():
        for kw in spec["keywords"]:
            all_keywords[kw.lower()] = cat
    combined = re.compile(
        r"(?i)(?<![a-z0-9_])(" + "|".join(re.escape(k) for k in all_keywords)
                   + r")(?![a-z0-9_])"
    )

    results = {
        cat: CategoryResult(name=cat, note=spec["note"])
        for cat, spec in CATEGORIES.items()
    }
    files_scanned = 0

    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in SOURCE_SUFFIXES or not path.is_file():
            continue
        files_scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        per_file: dict[str, set[str]] = {}
        for m in combined.finditer(text):
            cat = all_keywords[m.group(1).lower()]
            per_file.setdefault(cat, set()).add(m.group(1).lower())
        for cat, kws in per_file.items():
            r = results[cat]
            r.total_hits += len(kws)
            r.files.add(rel)
            r.keywords_hit.update(kws)

    return list(results.values()), files_scanned


def render_markdown(root_label: str, results: list[CategoryResult],
                    files_scanned: int, top: int) -> str:
    lines = [
        "# 静态关键字扫描报告",
        "",
        f"- **扫描根目录：** `{root_label}`（Jadx 导出 sources）",
        f"- **扫描文件数：** {files_scanned}",
        "- **产出方式：** `python scripts/static/scan.py`（见 scripts/static/README.md）",
        "- **口径说明：** 只统计文件路径与命中数，不含源码摘录；"
        "静态命中 ≠ 运行时必然调用，以动态证据为准。",
        "",
        "## 分类命中汇总",
        "",
        "| 检查项 | 命中文件数 | 命中关键字数 | 命中关键字（示例） |",
        "|--------|-----------|-------------|-------------------|",
    ]
    for r in results:
        kws = ", ".join(sorted(r.keywords_hit)[:8]) or "—"
        lines.append(
            f"| {r.name} | {len(r.files)} | {r.total_hits} | {kws} |"
        )
    lines += ["", "（命中关键字数 = 去重后的关键字种类数，非出现次数）", ""]
    lines += ["## 明细（每类最多列前 %d 个文件）" % top, ""]
    for r in results:
        if not r.files:
            continue
        lines += [f"### {r.name}", "", f"> {r.note}", ""]
        for f in sorted(r.files)[:top]:
            lines.append(f"- `{f}`")
        if len(r.files) > top:
            lines.append(f"- … 共 {len(r.files)} 个文件（其余略）")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sources", type=Path, help="Jadx 导出的 sources 目录")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="Markdown 报告输出路径（缺省打印到 stdout）")
    ap.add_argument("--top", type=int, default=DEFAULT_TOP,
                    help=f"每类最多列出的文件数（默认 {DEFAULT_TOP}）")
    ap.add_argument("--label", default=None,
                    help="报告里显示的扫描根目录标签（默认取目录名；"
                         "避免写入本机绝对路径）")
    args = ap.parse_args(argv)

    root = args.sources
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    results, files_scanned = scan_tree(root)
    label = args.label or root.name
    md = render_markdown(label, results, files_scanned, args.top)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(md, encoding="utf-8")
        print(f"wrote {args.output} ({files_scanned} files scanned)")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
