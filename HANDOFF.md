# Handoff — App Privacy Audit

> 交接说明 · 最后更新：2026-09-17  
> 仓库：https://github.com/ConradLu2740/app-privacy-audit  
> 本地：`<repo-root>\app-privacy-audit`（用 `git rev-parse --show-toplevel` 查）

> **v1.0 已发布（tag `4f36413`）。** 详见 [docs/DOD-self-check.md](docs/DOD-self-check.md)。  
> 文档以下部分是「v1.0 决策前的施工日志」，用于回顾设计权衡与现场记录；后续维护请看 README + 06 章「后续工作」。

---

## 1. 一句话现状（v1.0）

单人 Android 隐私审计作品集已交付 v1.0：**A3 NewPipe 三线闭环 + A1/A2 静态 + 政策对照 + LLM 合规引擎**；A1/A2 动态**已明确放弃**（真机无 root + 商业壳，已写进 DoD 自检与 06 章「后续工作」）。

---

## 2. 项目意图（已锁定，勿漂移）

| 项 | 决定 |
|----|------|
| 目标 | GitHub 作品集，证明会做 App 隐私合规检测 |
| 是否参赛 | **否**（选题来自省赛企业命题，但不报名） |
| 人力 | 单人 |
| 交付 | 深度报告 + 可复现 Frida 脚本 + 脱敏证据 + 规范文档 |
| 非目标 | 检测平台、海量扫描、产品化、竞赛答辩稿 |
| 样本策略 | 商业 2 款深挖 + 开源 1 款动态对照 |

完整 Intent/Spec/Plan：仓库内 `docs/intent-spec-plan.md`。

---

## 3. 已完成

### 工程与方法

- [x] 仓库骨架（README / LICENSE / .gitignore / docs / checklists / scripts / evidence）
- [x] 检查清单 v1（S 静态 / D 动态 / T 流量 / C 政策）
- [x] 方法论 + 合规方法 + 环境说明
- [x] Frida 脚本集（`device_id` / `location` / `contacts` / `clipboard` / `packages` / `sensors_audio` / `all_hooks`），已适配 **Frida 17**（无 `--no-pause`）
- [x] 证据规范与编号（`E-<app>-sta/dyn/trf/pol-nn`）

### 样本

| ID | 应用 | 包名 | 版本 | SHA-256（完整见 01） | 状态 |
|----|------|------|------|----------------------|------|
| A1 | 墨迹天气 | `com.moji.mjweather` | 9.0942.02 | `62DD0E3A…090DB7` | 静态完成；动态受阻 |
| A2 | 豆瓣 | `com.douban.frodo` | 7.133.0 | `0DB1996A…FDA9FDF` | 静态完成；动态受阻 |
| A3 | NewPipe | `org.schabi.newpipe` | 0.29.1 | `1D66D19E…1A84B7E8` | **三线闭环** |

### 分析结论摘要

**A1 墨迹**  
- 权限：精确定位 + 后台定位 + 活动识别 + 相机等；无通讯录/短信/READ_PHONE_STATE  
- 静态：OAID/设备标识线索极多；友盟/个推/穿山甲/高德/百度等 SDK  
- 动态：x86_64 AVD 无法启动；真机 Gadget 重打包后壳校验杀进程  
- 流量：**受阻** — 卡 splash，未能进入主界面采集  
- 证据：`E-A1-sta-01`、`E-A1-dyn-01/02`、`E-A1-trf-01`（受阻）

**A2 豆瓣**  
- 权限：定位、相机、录音、**QUERY_ALL_PACKAGES**  
- 静态：自研 `com.douban.push` deviceId；剪贴板代码较多；友盟/京东/阿里 mtop 等  
- 动态：可启动；Frida attach 后进程自杀；壳=网易易盾 NIS  
- 流量：**仅豆瓣自有域名**（frodo/amonsul/img*.doubanio.com），60s 未见第三方 SDK  
- 证据：`E-A2-sta-01`、`E-A2-dyn-01/02`、`E-A2-trf-01`

**A3 NewPipe**  
- 权限极少，无定位/电话/通讯录/OAID 簇  
- 动态 30s 剧本：D-* 均为**未观测到**；进程全程存活  
- 政策（GDPR 版）与观测**一致**；崩溃上报路径未实测  
- 流量：仅 `www.youtube.com`，无第三方追踪域名（PCAPdroid 连接级）  
- 证据：`E-A3-sta-01`、`E-A3-dyn-01/02`、`E-A3-pol-01`、`E-A3-trf-01`

### GitHub

- 已 `gh repo create` + push `master`
- Topics：`android` `frida` `privacy` `security` `reverse-engineering` `mobile-security` `jadx` `appsec` `privacy-policy` `static-analysis`
- 双语 README：`README.md`（EN）+ `README.zh-CN.md`（中文）

---

## 4. 未完成 / v1.0 决策

| 项 | v1.0 状态 | 后续建议 |
|----|----------|----------|
| A1/A2 动态复测 | **放弃**（无 root 路径；壳 = 爱加密 + 网易易盾 NIS） | 真机 root + 脱壳或更换样本策略 |
| A1/A2 政策对照 | ✅ 完成（`E-A1-pol-01` / `E-A2-pol-01`） | — |
| 流量 T-*（A1） | ✅ 完成（2026-09-17 首启复测：535 连接 / 74 主机 / 50 明文 HTTP，E-A1-trf-02） | 登录态复测覆盖未登录盲区 |
| 流量 T-*（A2/A3） | ✅ 完成（60s / 30s 连接级） | 登录态复测覆盖未登录盲区 |
| 报告 04/06 章 | ✅ 完成（非骨架） | — |
| 结论章修复建议 | ✅ 完成（F-01..F-10） | — |
| 检查清单逐项勾满 | ✅ 完成（`checklists/privacy-checklist.md`） | — |
| LLM 合规引擎 | ✅ 完成（`audit/`，21 项测试） | 增加 eval set / 性能评测 |
| v1.0 tag | ✅ `4f36413` | — |

---

## 5. 本机环境（恢复用）

### 路径

```text
仓库     <repo-root>\app-privacy-audit
实验室   <user-home>\privacy-lab\
  apks\   A1/A2/A3 APK（勿提交 Git）
  tools\  frida-server, jadx\, apktool.jar, frida-gadget-*.so, debug.keystore
  gadget-work\  A1/A2 反编译 + gadget 注入工作目录（勿提交）
  jadx-moji\  jadx-douban\   # 已反编译输出
  logs\   Frida/logcat 原始日志
SDK      c:\trae_solo\workspace\android-studio\android-sdk
AVD      privacy-api30  (Android 11, x86_64, google_apis)  # 仅 A3 可用
真机     小米 14 Ultra arm64-v8a 无 root（序列号不入库，用 `adb devices` 查）
Python   C:\Program Files\Python311\python.exe
Frida    17.18.0 (pip frida-tools + 设备端 server + gadget)
Jadx     1.5.1
apktool  2.11.1
```

### 常用命令

```powershell
# 模拟器
& "c:\trae_solo\workspace\android-studio\android-sdk\emulator\emulator.exe" -avd privacy-api30
adb devices
adb root
adb shell "/data/local/tmp/frida-server -D &"
frida-ps -U

# A3 动态（推荐 attach，不要盲目 spawn）
adb shell pm clear org.schabi.newpipe
adb shell am start -n org.schabi.newpipe/.MainActivity
adb shell pidof org.schabi.newpipe
cd <repo-root>\app-privacy-audit
frida -U -p <pid> -l scripts\frida\all_hooks.js

# 注意
# - Frida 17 不要 --no-pause
# - Python API 在 spawn 后立刻 load 可能 Java undefined；CLI attach 更稳
# - A1 本 AVD 起不来；A2 attach 会自杀
# - 真机无 root：frida-server 无法 attach 商业 App；Gadget 重打包被壳杀
```

详见 `docs/environment.md`。

---

## 6. Git 提交脉络（master · 至 v1.0）

| Commit | 内容 |
|--------|------|
| `ba11b7e` | 初始骨架 |
| `f541d55` | 候选样本调研 |
| `792a1f0` | 环境文档 + Frida17 修复 |
| `197cd36` | 锁定 A1/A2 |
| `f2b3a47` | A1/A2 静态分析 |
| `2d3b028` | 清单进度 |
| `3dbb0e9` | A1/A2 动态受阻取证 |
| `827164c` | A3 对照样本 |
| `79a872e` / `a7cfded` | A3 动态文档补全 |
| `4bcfc5a` | A3 政策对照 |
| `fb18586` | README 重写（可复现向） |
| `311fa72` | Mermaid 图 |
| `53df24e` | 英文 README + 中文 zh-CN |
| `e319628` | 推送前敏感信息脱敏 |
| `2eaf423` | A2 流量证据（仅自有域名）+ A1 流量受阻取证 |
| `2329b64` | A3 流量证据（仅 `www.youtube.com`） |
| `eb30094` | 真机 Gadget 重打包文档化（爱加密 + 网易易盾均杀进程） |
| `a7cfded`..`4bcfc5a` | A3 三线闭环 |
| `fb18586`..`311fa72` | README 重写 + Mermaid 图 |
| `6474a1e` | 添加 HANDOFF（v1.0 前版本） |
| `64b3d22` | 移除个人信息 + 本地用户名路径 |
| `10b4926` | 政策对照 + 报告 04/06 章节 fill |
| `26cd5be` | LLM 合规研判引擎 |
| **`1501687`** | **v1.0 收尾：checklist 全勾完 + A1/A2 政策对照补完 + 摘掉骨架标签 + DoD 自检** |
| **`v1.0`** | **tag `4f36413` · 作品集首版** |

工作区干净；远程 `origin/master` 待 `git push origin master --tags`。

---

## 7. 后续维护（v1.0 之后）

1. `git pull` + `git fetch --tags`，确认 `v1.0` tag 在本地
2. **v1.0 之后做扩展时**，先看 [docs/DOD-self-check.md](docs/DOD-self-check.md) 顶部「总体结论」段了解当前能力范围
3. **不要把 HANDOFF 当唯一真相**：所有「未完成」都已 v1.0 化；新工作请按 [README.md](README.md) + [docs/report/06-findings-and-fixes.md §5](docs/report/06-findings-and-fixes.md) 推进
4. 接手扩展时先确认：是否仍单人 / 是否仍不参赛 / 是否仍按 GitHub 作品集标准（参见 [Intent Spec §1](docs/intent-spec-plan.md)）
5. 按目标选一条线：  
   - **有 ARM 真机 + 脱壳能力** → 重跑 A1/A2 动态，补 D-*（环境：`docs/environment.md`）  
   - **有登录态场景** → A2 登录后流量复测  
   - **扩展样本** → 按 [docs/sample-candidates.md](docs/sample-candidates.md) 选样，复制 evidence 模板
6. 证据一律脱敏后进 `evidence/<pkg>/`，报告只引用编号
7. 提交时说明「测了什么、没测什么」

---

## 8. 风险与约定（交接必读）

- 不提交 APK / 原始 PCAP / 未脱敏日志  
- 静态命中 ≠ 违规；动态未观测 ≠ 不存在  
- 受阻必须写清原因（ABI / 壳 / 反注入）  
- 法规条文引用前核对原文，不编条号  
- 研究仅限自有设备上的公开分发应用  

---

## 9. 联系上下文

- 竞赛通知联系人（仅背景，本项目不参赛）：详见竞赛通知原文（不入库）  
- 官网：https://zjnisc.hdu.edu.cn/  
- 赛题原文：上级目录或 `assets/qiye-mingti.docx`（竞赛附件1，本地曾下载）

---

## 10. 下次开工检查清单（v1.0 后扩展时）

- [ ] `git status` 干净且 `origin` 同步（`v1.0` tag 在本地）  
- [ ] 重读 `docs/DOD-self-check.md` 顶部「总体结论」了解能力范围  
- [ ] 重读 `README.md` 与 `Intent Spec §1` 确认是否仍按 GitHub 作品集标准  
- [ ] 模拟器/真机可 `adb devices`（如做动态）  
- [ ] `frida --version` 与设备端 server 一致（如做动态）  
- [ ] A3 能 attach 不自杀（环境健康探针）  
- [ ] 明确本轮只做一条线（新样本 / 动态复测 / 流量 / 政策 / 文档）  

— v1.0 交接完毕 —
