#!/usr/bin/env python3
"""图 2：A1 明文 HTTP 端点分布；图 3：三款 App 流量对照。

数据口径：
- 图 2：E-A1-trf-02（50 条明文 HTTP，按目标端点分组）
- 图 3：E-A1-trf-02 / E-A2-trf-01 / E-A3-trf-01（未登录前台窗口的连接级观测）
用法：python scripts/diagrams/plot_traffic_figures.py
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager

BASE = Path(__file__).resolve().parents[2]
DIAGRAMS = BASE / "assets" / "diagrams"

for candidate in ("Microsoft YaHei", "SimHei"):
    if any(candidate.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = candidate
        break
plt.rcParams["axes.unicode_minus"] = False

C_OWN = "#78909C"    # 自有：灰蓝
C_THIRD = "#D32F2F"  # 第三方：红
C_GRAY = "#B0BEC5"


def save(fig: plt.Figure, name: str, title: str, caption: str) -> None:
    fig.suptitle(title, fontsize=13.5, color="#1A237E", weight="bold", y=0.99)
    fig.text(0.5, -0.02, caption, ha="center", fontsize=8.5, color="#78909C")
    out = DIAGRAMS / name
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white", pad_inches=0.18)
    plt.close(fig)
    print("wrote", out)


# ---- 图 2：明文 HTTP 端点分布 ---------------------------------------------
HTTP_HOSTS = Counter({
    "v1.log.moji.com": 13, "cdn.moji.com": 10, "oss4bpc.moji.com": 7,
    "v2.log.moji.com": 5, "oss4liview.moji.com": 4, "ad.api.moji.com": 4,
    "adlaunch.moji.com": 1, "cdn.moji002.com": 1, "coapi.moji.com": 1,
    "apps.mojicdn.com": 1, "bjimp.voiceads.cn": 1,
    "p26-be-pack-sign.pglstatp-toutiao.com": 1, "stat.moji.com": 1,
})
THIRD_HTTP = {"bjimp.voiceads.cn", "p26-be-pack-sign.pglstatp-toutiao.com"}

items = sorted(HTTP_HOSTS.items(), key=lambda kv: kv[1])
names = [k for k, _ in items]
vals = [v for _, v in items]
colors = [C_THIRD if n in THIRD_HTTP else C_OWN for n in names]

fig, ax = plt.subplots(figsize=(9.5, 5.4))
fig.patch.set_facecolor("white")
bars = ax.barh(names, vals, color=colors, height=0.6)
for bar, v in zip(bars, vals):
    ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
            f"{v} 条", va="center", fontsize=9, color="#37474F")
ax.set_xlabel("明文 HTTP 连接数（条）", fontsize=10, color="#37474F")
ax.set_xlim(0, max(vals) * 1.25)
ax.set_title("50 条明文 HTTP 按目标端点分布（13 个端点）",
             fontsize=12, color="#263238", pad=12)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(colors="#37474F", labelsize=9)
ax.xaxis.grid(True, color="#ECEFF1", linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(handles=[
    mpatches.Patch(color=C_OWN, label="墨迹自有（12 个端点 / 48 条）"),
    mpatches.Patch(color=C_THIRD, label="第三方（2 个端点 / 2 条）"),
], loc="lower right", frameon=False, fontsize=9)
save(fig, "a1-plaintext-http.png",
     "图 2 · 墨迹天气明文 HTTP 端点分布（风险项 F-10）",
     "数据来源：PCAPdroid 连接级捕获，证据编号 E-A1-trf-02 · 2026-09-17 · 未登录")


# ---- 图 3：三款 App 流量对照 -----------------------------------------------
APPS = ["A1 墨迹天气\n(60s)", "A2 豆瓣\n(60s)", "A3 NewPipe\n(30s)"]
THIRD_HOSTS = [39, 0, 0]
PLAINTEXT = [50, 0, 0]
OWN_HOSTS = [35, 8, 1]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.2))
fig.patch.set_facecolor("white")
import numpy as np
x = np.arange(len(APPS))
w = 0.38

b1 = ax1.bar(x - w / 2, OWN_HOSTS, w, label="自有域名", color=C_OWN)
b2 = ax1.bar(x + w / 2, THIRD_HOSTS, w, label="第三方域名", color=C_THIRD)
for bars in (b1, b2):
    for bar in bars:
        ax1.text(bar.get_width() / 2 + bar.get_xy()[0], bar.get_height() + 0.8,
                 f"{int(bar.get_height())}", ha="center", fontsize=10,
                 color="#37474F", weight="bold")
ax1.set_xticks(x, APPS, fontsize=10)
ax1.set_ylabel("独立主机数（个）", fontsize=10, color="#37474F")
ax1.set_ylim(0, max(THIRD_HOSTS + OWN_HOSTS) * 1.25)
ax1.set_title("观测窗口内连接的独立主机数", fontsize=12, color="#263238", pad=12)
ax1.spines[["top", "right"]].set_visible(False)
ax1.tick_params(colors="#37474F")
ax1.yaxis.grid(True, color="#ECEFF1", linewidth=0.8)
ax1.set_axisbelow(True)
ax1.legend(frameon=False, fontsize=9, loc="upper right")

bars = ax2.bar(APPS, PLAINTEXT, width=0.5,
               color=[C_THIRD, C_GRAY, C_GRAY])
for bar, v in zip(bars, PLAINTEXT):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
             f"{v} 条", ha="center", fontsize=10, color="#37474F", weight="bold")
ax2.set_ylabel("明文 HTTP 连接数（条）", fontsize=10, color="#37474F")
ax2.set_ylim(0, max(PLAINTEXT) * 1.3)
ax2.set_title("明文 HTTP 连接", fontsize=12, color="#263238", pad=12)
ax2.spines[["top", "right"]].set_visible(False)
ax2.tick_params(colors="#37474F", labelsize=10)
ax2.yaxis.grid(True, color="#ECEFF1", linewidth=0.8)
ax2.set_axisbelow(True)

save(fig, "traffic-apps-comparison.png",
     "图 3 · 三款 App 流量对照（均为未登录前台观测窗口）",
     "数据来源：E-A1-trf-02 / E-A2-trf-01 / E-A3-trf-01 · 2026-09-14 ~ 17 · 连接级口径，"
     "「未观测到」不等于「不存在」")
