# 静态分析辅助说明

本目录预留可选脚本（Python 等），用于从 Jadx 导出结果或 `aapt dump` 里批量搜敏感 API。

当前以 **Jadx-gui 人工检索 + 检查清单** 为主；脚本按需再补，避免过度工程。

## 推荐检索关键字（与清单 S-10… 对齐）

```text
getDeviceId
getImei
getMeid
getSubscriberId
getSimSerialNumber
ANDROID_ID
getMacAddress
getLastKnownLocation
requestLocationUpdates
ContactsContract
ClipboardManager
getInstalledPackages
MODE_WORLD_READABLE
http://
addJavascriptInterface
```

## aapt 权限速查（可选）

```bash
aapt dump permissions sample.apk
aapt dump badging sample.apk | head
```

## 产出

- 权限表 → 检查清单 S-01…  
- 调用点截图/类名 → `evidence/<pkg>/static/`  
- 假设 `H-xx` 写入报告 `02-static-analysis.md`  
