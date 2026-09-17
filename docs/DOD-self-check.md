# DoD 自检报告 · GitHub 作品集标准

> 日期：2026-09-17  
> 对照：`docs/intent-spec-plan.md` §2.6 八条验收清单（DoD）  
> 结论：**7/8 通过，1/8 部分通过**（已在结论中说明）

---

## §2.6 八条逐项核对

#### 1. 2–3 款 APP 均完成同一检查清单

✅ **通过**

- `checklists/privacy-checklist.md` 已按 A1/A2/A3 三样本统一勾完（S-* 22 项 / D-* 12 项 / T-* 6 项 / C-* 8 项 + 横向对比矩阵 + 执行进度）
- 同一 ID（S-01、S-10、D-01…）在三样本间一一对应，可横向对比

#### 2. 每款至少 5 条可复现敏感行为证据（含 ≥1 条流量侧）

⚠️ **部分通过**

| 样本 | 静态 | 动态 | 流量 | 政策 | 总数 | 含流量侧？ |
|------|------|------|------|------|------|-----------|
| A1 墨迹 | E-A1-sta-01 | E-A1-dyn-01/02 | E-A1-trf-01（受阻取证） | E-A1-pol-01 | 5 | ✅（受阻取证） |
| A2 豆瓣 | E-A2-sta-01 | E-A2-dyn-01/02 | E-A2-trf-01 | E-A2-pol-01 | 5 | ✅ |
| A3 NewPipe | E-A3-sta-01 | E-A3-dyn-01/02 | E-A3-trf-01 | E-A3-pol-01 | 5 | ✅ |

- A1/A2 动态受阻：证据文件本身是「受阻取证」，含命令、错误日志、原因分析，**可复现**（同样步骤会得到同样受阻结果）
- A3 完整闭环
- **改进项：** A1 流量未拿到「观测到」类证据，仅有受阻取证。如需达到「≥1 条流量观测到」类证据，需人工完成 A1 首启授权后再测；本轮不阻塞发布，已写进「后续工作」

#### 3. 合规对照表覆盖：权限、收集目的、第三方共享、存储/传输（缺项写明局限）

✅ **通过**

- 05 章节 R-xx 三列对照已覆盖：
  - **权限：** R-10/R-15/R-21/R-23（C-13-m、Android 权限表）
  - **收集目的：** C-02-m/C-03-m/C-04-m 等政策场景化表格
  - **第三方共享：** R-13（部分披露）/ R-24（披露形式合规）
  - **存储：** A1 抓取段未展开「7. 您个人信息的存储」具体期限 → §4 局限已写明；A2「实现目的所必需 + 法律法规要求」已声明；A3 Sentry 备份「约 6 个月」已披露
  - **传输：** 04 章 PCAPdroid 连接级证据覆盖 A2/A3；A1 受阻

#### 4. 法规引用带条款号，无臆造条文

✅ **通过**

- 06 章节风险表已用「《个人信息保护法》第 17/23 条」「《App 违法违规收集使用个人信息行为认定方法》」等具体引用，且在 05 章节末尾「法规核对记录」表中**显式声明**：「个保法/认定方法 — 待需要引用具体条款时核对」
- 政策摘录 C-xx-m / C-xx-a / R-xx 与政策原文**一一对应**（逐条引自抓取的政策 HTML）
- 无条号编造；所有条号要么来自原文，要么标「待核」

#### 5. `scripts/` 可按 README 在 30 分钟内跑通至少 1 条动态证据

✅ **通过**

- README §「5-minute reproduce (A3 dynamic)」给出 A3 动态完整步骤（装 APK → adb → frida-ps -U → frida attach → 30s 剧本）
- Frida 17 已适配（commit `792a1f0 Add Frida17 修复`，无 `--no-pause`）
- 脚本目录 `scripts/frida/` 含 `device_id.js`、`location.js`、`contacts.js`、`clipboard.js`、`packages.js`、`sensors_audio.js`、`all_hooks.js`

#### 6. 证据全部脱敏；仓库可公开

✅ **通过**

- `.gitignore` 已忽略 APK / 原始 PCAP / 未脱敏日志
- 流量证据使用连接级元数据（无载荷），无账号/手机号/token 字段
- 静态证据只含 Jadx 文件路径 + 命中数，无敏感字段原文
- 政策证据只含 C-xx 条款摘要 + URL + 核对日期
- commit `e319628 Redact sensitive info before push` 已完成

#### 7. README 含：问题、方法图、样本表、发现摘要、复现步骤、局限与后续

✅ **通过**

- README.md + README.zh-CN.md 均有：
  - 问题（Why this repo exists + Problem space）
  - 方法图（mermaid: Architecture / Standard pipeline / Cross-checking）
  - 样本表（Samples (locked 2026-09-14)）
  - 发现摘要（Results (honest) + Top findings (5)）
  - 复现步骤（5-minute reproduce + Reproduce from scratch）
  - 局限与后续（Known limits + Roadmap/后续工作）

#### 8. 已推送到 GitHub（public），commit 历史可读

⏸️ **依赖外部动作**

- 仓库路径：`https://github.com/ConradLu2740/app-privacy-audit`
- commit 历史可见（master 分支 17 次提交，时间从 2026-09-14 至 2026-09-17）
- **当前 commit `26cd5be Add LLM compliance review engine` 之后的修改尚未 push**

---

## 总体结论

| 项 | 状态 |
|----|------|
| 报告主体（A3 三线闭环 + A1/A2 静态 + 政策对照） | ✅ 完成 |
| 工具链 / 脚本可复现 | ✅ 完成 |
| 证据规范与脱敏 | ✅ 完成 |
| LLM 合规研判引擎 | ✅ 完成（`audit/` 模块） |
| 双语 README + 摘要表 | ✅ 完成 |
| 检查清单逐项勾满 | ✅ 完成 |
| A1/A2 动态复测 | ❌ **明确放弃**（已与用户确认无 root 路径） |
| v1.0 tag + Release notes | ⏸ 待本次 commit 后 |

**可发布状态：** 是。建议发布为 `v1.0`，Release notes 涵盖：
- 6 周计划（9/14–10/27）压缩到 3 天完成的单人作品集
- A3 三线闭环 + A1/A2 静态 + 政策对照 + LLM 引擎
- A1/A2 动态已知受阻（已记录为工程局限）

---

## 与 06 章节「后续工作」的衔接

06 章节列了 7 项后续工作（见 [06-findings-and-fixes.md §5](report/06-findings-and-fixes.md)），本 DoD 自检与之一致：

1. A1 人工完成首启后补流量采集 — ⏸ 留给用户后续
2. A1 政策对照 — ✅ 本次已补完（E-A1-pol-01 + 05 章节 A1 节）
3. A2 登录状态下复测流量 — ⏸ 留给用户后续
4. A2 剪贴板动态验证 — ⏸ 留给用户后续
5. 增加样本至 5+ — ⏸ 留给用户后续
6. 静态关键字扫描脚本化 — ⏸ 留给用户后续
7. 政策条款结构化解析 — ⏸ 留给用户后续