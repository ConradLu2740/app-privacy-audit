# App Privacy Audit

单人可复现的 **Android 应用隐私数据泄露检测** 方法与案例研究。

> 选题源自第九届浙江省大学生网络与信息安全竞赛作品挑战赛企业命题  
> （命题企业：浙江省质量科学研究院）。本仓库**不用于正式参赛**，按开源作品集标准维护。

## 这个项目在解决什么问题

移动 App 大量收集设备标识、位置、通讯录等个人信息，常见风险包括：

- 权限过度索取，与功能无关
- 隐私政策「说一套、做一套」
- 敏感数据明文存储或明文/弱加密传输

本项目用 **静态逆向 + 动态 Hook + 流量分析** 三条证据线，对真实应用商店样本做可复现审计，并把「政策文本 ↔ 运行时行为 ↔ 法规条款」对齐成可核对结论。

## 方法总览

```text
样本锁定
   │
   ├─ 静态 (Jadx) ──► 权限 / 敏感 API / SDK 线索 ──► 假设 H-xx
   │                                                      │
   ├─ 动态 (Frida) ◄──────────────────────────────────────┘
   │         │
   │         └─► 运行时调用证据（时间点 / 调用栈）
   │
   ├─ 流量 (代理 / PCAP) ──► 明文字段 / 超范围传输
   │
   └─ 合规对照 ──► 政策条款 C-xx × 行为 E-xx × 法规条文
                        │
                        └─► 风险分级 + 修复建议
```

详见 [docs/methodology.md](docs/methodology.md) 与 [checklists/privacy-checklist.md](checklists/privacy-checklist.md)。

## 样本（已锁定 2026-09-14）

| ID | 应用 | 包名 | 版本 | 渠道 | 状态 |
|----|------|------|------|------|------|
| A1 | 墨迹天气 | `com.moji.mjweather` | 9.0942.02 | 官网 CDN | 已锁定；静态深挖 / 动态受阻 |
| A2 | 豆瓣 | `com.douban.frodo` | 7.133.0 | 官网下载 | 已锁定；静态深挖 / 反注入受阻 |
| A3 | NewPipe（对照） | `org.schabi.newpipe` | 0.29.1 | F-Droid | 已锁定；**动态链路可复现** |

详细哈希与 Jadx 结论见 [docs/report/01-samples.md](docs/report/01-samples.md)。

## 结果摘要

| 样本 | 高风险 | 中风险 | 低风险/观察 | 备注 |
|------|--------|--------|-------------|------|
| A1 | — | — | — | 静态完成；动态受阻（ARM+壳） |
| A2 | — | — | — | 静态完成；动态受阻（反注入） |
| A3 | 0 | 0 | 窗口内无敏感 API；政策与观测一致 | 静态+动态+政策对照完成 |

## 快速开始（复现一条动态证据）

1. 按 [docs/environment.md](docs/environment.md) 启动 AVD `privacy-api30` 并拉起 `frida-server`。
2. 安装目标 APK（自行从官方渠道获取，**勿将 APK 提交到本仓库**）。
3. 运行：

```bash
frida -U -f com.douban.frodo -l scripts/frida/all_hooks.js
```

4. 操作 App，观察控制台输出；将脱敏日志按 [evidence/README.md](evidence/README.md) 规范归档。

> Frida 17 默认 spawn 后自动恢复，无需 `--no-pause`。

## 仓库结构

```text
app-privacy-audit/
├── README.md
├── docs/                 # 方法论、环境、完整报告
├── checklists/           # 统一隐私检查清单
├── scripts/frida/        # 动态 Hook 脚本
├── evidence/             # 脱敏证据（按样本分目录）
└── assets/               # 非敏感图片等
```

## 声明与边界

- 仅在**自有测试设备/模拟器**上对公开分发应用做安全研究与合规学习。
- 不包含、不传播任何完整 APK 与原始含隐私流量。
- 结论基于特定版本与观测窗口；未观测到 ≠ 不存在。
- 法规引用需人工核对原文，存疑处标注「待核」。

## License

[MIT](LICENSE)
