# 静态分析辅助说明

本目录提供可复现的静态关键字扫描脚本 `scan.py`，替代纯人工 Jadx 翻检，
产出对齐检查清单 S-* 项的 Markdown 报告（只含文件路径与命中数，不含源码摘录，
可直接进 `evidence/<pkg>/static/`）。

## scan.py 用法

```bash
# 前置：jadx 反编译
jadx -d <out-dir> sample.apk        # 产出 <out-dir>/sources

# 扫描（--label 避免把本机绝对路径写进报告）
python scripts/static/scan.py <out-dir>/sources --label jadx-<name>/sources -o report.md
```

实测耗时（2026-09-17，本机）：A1 墨迹 27,692 文件约 24s；A2 豆瓣 34,809 文件约 4min。

## 关键字分类（与清单 S-* 对齐）

| 分类 | 检查项 | 覆盖要点 |
|------|--------|---------|
| 设备标识 | S-10 | IMEI/IMSI/MAC/OAID/UMeng 等设备标识线索 |
| 定位 | S-12 | LocationManager / FusedProvider / Geofence |
| 通讯录 | S-13 | ContactsContract / READ_CONTACTS |
| 剪贴板 | S-14 | ClipboardManager / PrimaryClip 读写与监听 |
| 应用列表 | S-15 | getInstalledPackages / QUERY_ALL_PACKAGES / UsageStats |
| 存储/文件 | S-20 | 外部存储 / WORLD_READABLE 等危险模式 |
| 网络安全 | S-21 | 明文 http:// / WebView addJavascriptInterface / 自定义证书校验 |
| 三方 SDK 指纹 | S-22 | 友盟/阿里/腾讯/个推/穿山甲/高德/百度/Sentry 等包名类名指纹 |

关键字表内嵌在 `scan.py` 的 `CATEGORIES` 中，按需增补。

## 已产出证据

| 证据 | 样本 | 说明 |
|------|------|------|
| `evidence/com.moji.mjweather/static/E-A1-sta-02.md` | A1 墨迹 | 与 E-A1-sta-01 人工结论一致 |
| `evidence/com.douban.frodo/static/E-A2-sta-02.md` | A2 豆瓣 | 与 E-A2-sta-01 人工结论一致 |

## 口径与局限

- 静态命中 ≠ 运行时必然调用；以动态证据为准
- 词边界匹配（字母数字下划线），短词不会误匹配标识符内部
- 命中次数为「去重关键字种类数」，非出现次数
- 关键字表是常见 API/SDK 指纹集合，非全量；人工复核仍是最终口径

## aapt 权限速查（可选）

```bash
aapt dump permissions sample.apk
aapt dump badging sample.apk | head
```

## 产出流向

- 扫描报告 → `evidence/<pkg>/static/E-<app>-sta-nn.md`
- 假设 `H-xx` 写入报告 `02-static-analysis.md`
