# 00 · 报告总览

> 状态：骨架（样本与结论待分析后填写）  
> 方法论：[../methodology.md](../methodology.md) · 合规：[../compliance.md](../compliance.md)

## 1. 背景与问题

移动 App 是个人信息收集的主要入口。常见风险包括权限过度索取、隐私政策与行为不一致、敏感数据明文存储/传输等。本报告对选定的真实应用商店样本进行三线（静态 / 动态 / 流量）检测，并给出合规对照与修复建议。

## 2. 范围

| 项 | 说明 |
|----|------|
| 样本数量 | 2–3（见 [01-samples.md](01-samples.md)） |
| 测试环境 | 见 [../environment.md](../environment.md) |
| 时间窗口 | （填写实际测试周） |
| 不在范围 | 自动化平台、全商店扫描、内核级对抗、生产环境攻击 |

## 3. 方法摘要

1. Manifest / Jadx 静态检索 → 假设 H-xx  
2. Frida 运行时验证 → 证据 E-xx-dyn  
3. 代理/设备侧抓包 → E-xx-trf  
4. 隐私政策拆解 → C-xx；三列对照 → 风险与修复  

详细清单：[../../checklists/privacy-checklist.md](../../checklists/privacy-checklist.md)

## 4. 总体发现（分析完成后填写）

| 样本 | 高 | 中 | 低/观察 | 一句话 |
|------|----|----|---------|--------|
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |

## 5. 局限

- 未观测到 ≠ 不存在（路径/版本/权限状态依赖）  
- HTTPS 未解密场景下的传输结论有限（按样本写明）  
- 单次安装、单一系统版本  
- 法规条文以核对日现行文本为准  

## 6. 目录

| 章节 | 文件 |
|------|------|
| 样本 | [01-samples.md](01-samples.md) |
| 静态 | [02-static-analysis.md](02-static-analysis.md) |
| 动态 | [03-dynamic-analysis.md](03-dynamic-analysis.md) |
| 流量 | [04-traffic-analysis.md](04-traffic-analysis.md) |
| 合规 | [05-compliance-review.md](05-compliance-review.md) |
| 结论与修复 | [06-findings-and-fixes.md](06-findings-and-fixes.md) |
