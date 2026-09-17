#!/usr/bin/env python3
"""A1 流量数据可视化：厂商连接分布 + 自有/第三方占比。

数据来自 evidence/com.moji.mjweather/traffic/E-A1-trf-02.md（PCAPdroid 首启 60s）。
用法：python scripts/diagrams/plot_a1_traffic.py
产出：assets/diagrams/a1-traffic-overview.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "assets" / "diagrams" / "a1-traffic-overview.png"

# 中文字体（Windows 自带）
for candidate in ("Microsoft YaHei", "SimHei"):
    if any(candidate.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = candidate
        break
plt.rcParams["axes.unicode_minus"] = False

# (厂商, 连接数, 流量 KB, 类别) —— 数据口径见 E-A1-trf-02 §3
VENDORS = [
    ("墨迹自有",            295, 11543, "own"),
    ("京东",                 69,   419, "ads"),
    ("腾讯广告 GDT",         49,   887, "ads"),
    ("高德",                 40,  4659, "sdk"),
    ("穿山甲/字节",          27,  1569, "ads"),
    ("百度广告",              9,    32, "ads"),
    ("个推",                  8,    29, "sdk"),
    ("阿里 tanx",             5,    98, "ads"),
    ("微信小程序云",          4,  1029, "sdk"),
    ("秒针监测",              4,    17, "ads"),
    ("友盟",                  3,    15, "sdk"),
    ("其他/未分类",          22,   340, "misc"),
]
COLORS = {
    "own":  "#78909C",   # 自有：灰蓝
    "ads":  "#D32F2F",   # 广告：红
    "sdk":  "#F9A825",   # 基础 SDK：琥珀
    "misc": "#B0BEC5",   # 其他：浅灰
}

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(11.5, 5.6), gridspec_kw={"width_ratios": [3, 1.4]}
)
fig.patch.set_facecolor("white")

# ---- 左：厂商连接分布 ----------------------------------------------------
names = [v[0] for v in VENDORS][::-1]
conns = [v[1] for v in VENDORS][::-1]
kbs = [v[2] for v in VENDORS][::-1]
colors = [COLORS[v[3]] for v in VENDORS][::-1]

bars = ax1.barh(names, conns, color=colors, height=0.62, edgecolor="none")
for bar, conn, kb in zip(bars, conns, kbs):
    ax1.text(
        bar.get_width() + 4, bar.get_y() + bar.get_height() / 2,
        f"{conn} 条 · {kb / 1024:.1f} MB" if kb >= 1024 else f"{conn} 条 · {kb} KB",
        va="center", fontsize=9, color="#37474F",
    )
ax1.set_xlabel("连接数（条）", fontsize=10, color="#37474F")
ax1.set_xlim(0, max(conns) * 1.32)
ax1.set_title("首启 60 秒各厂商连接分布（共 535 条 / 74 主机）",
              fontsize=12, color="#263238", pad=12)
ax1.spines[["top", "right"]].set_visible(False)
ax1.tick_params(colors="#37474F", labelsize=9.5)
ax1.xaxis.grid(True, color="#ECEFF1", linewidth=0.8)
ax1.set_axisbelow(True)

import matplotlib.patches as mpatches
legend = [
    mpatches.Patch(color=COLORS["own"], label="墨迹自有域名"),
    mpatches.Patch(color=COLORS["ads"], label="广告 SDK"),
    mpatches.Patch(color=COLORS["sdk"], label="基础服务 SDK"),
    mpatches.Patch(color=COLORS["misc"], label="其他"),
]
ax1.legend(handles=legend, loc="lower right", frameon=False, fontsize=9)

# ---- 右：自有 vs 第三方占比 ----------------------------------------------
own_total = sum(v[1] for v in VENDORS if v[3] == "own")
third_total = sum(v[1] for v in VENDORS if v[3] != "own")
wedges, _ = ax2.pie(
    [own_total, third_total],
    colors=[COLORS["own"], "#D32F2F"],
    startangle=90, counterclock=False,
    wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
)
ax2.text(0, 0.08, f"{third_total / (own_total + third_total):.0%}",
         ha="center", fontsize=26, color="#D32F2F", weight="bold")
ax2.text(0, -0.24, "第三方连接占比", ha="center", fontsize=10, color="#37474F")
ax2.set_title("连接归属", fontsize=12, color="#263238", pad=12)

fig.suptitle("图 1 · 墨迹天气（com.moji.mjweather 9.0942.02）首启后 60 秒流量画像",
             fontsize=13.5, color="#1A237E", weight="bold", y=0.99)
fig.text(0.5, -0.015,
         "数据来源：PCAPdroid 连接级捕获，证据编号 E-A1-trf-02 · 2026-09-17 · 未登录",
         ha="center", fontsize=8.5, color="#78909C")

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white", pad_inches=0.18)
print("wrote", OUT)
