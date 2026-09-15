# Handoff — App Privacy Audit

> 交接说明 · 最后更新：2026-09-15  
> 仓库：https://github.com/ConradLu2740/app-privacy-audit  
> 本地：`C:\Users\13906\XiaomiMiMoProjects\CTF\app-privacy-audit`

---

## 1. 一句话现状

单人 Android 隐私审计作品集：**A1/A2 商业样本静态完成、动态受阻已取证（含真机 Gadget 复测）；A3 NewPipe 静态+动态+政策闭环**；仓库双语 README + Mermaid 图已上 GitHub。

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
- 动态：x86_64 AVD 无法启动；**真机（小米14U）Gadget 重打包后壳校验杀进程**  
- 证据：`E-A1-sta-01`、`E-A1-dyn-01`、`E-A1-dyn-02`（受阻）

**A2 豆瓣**  
- 权限：定位、相机、录音、**QUERY_ALL_PACKAGES**  
- 静态：自研 `com.douban.push` deviceId；剪贴板代码较多；友盟/京东/阿里 mtop 等  
- 动态：可启动；Frida attach 后进程自杀；**壳=网易易盾 NIS，与 A1 同类加固**  
- 证据：`E-A2-sta-01`、`E-A2-dyn-01`、`E-A2-dyn-02`（受阻）

**A3 NewPipe**  
- 权限极少，无定位/电话/通讯录/OAID 簇  
- 动态 30s 剧本：D-* 均为**未观测到**；进程全程存活  
- 政策（GDPR 版）与观测**一致**；崩溃上报路径未实测  
- 证据：`E-A3-sta-01`、`E-A3-dyn-01/02`、`E-A3-pol-01`

### GitHub

- 已 `gh repo create` + push `master`
- Topics：`android` `frida` `privacy` `security` `reverse-engineering` `mobile-security` `jadx` `appsec` `privacy-policy` `static-analysis`
- 双语 README：`README.md`（EN）+ `README.zh-CN.md`（中文）

---

## 4. 未完成 / 明确不做优先

| 项 | 状态 | 建议优先级 |
|----|------|------------|
| A1/A2 动态复测 | 真机已试 Gadget，壳杀进程；**需 root 或脱壳** | 高（解锁 BL + Magisk） |
| A1/A2 政策对照 | 可先读政策，但一致性需动态 | 中 |
| 流量 T-*（任意样本） | 未配置 mitmproxy | 中 |
| 报告 04/06 章 | 仅骨架 | 随流量/结论补 |
| 结论章修复建议 | 未写 | 低（有完整证据后） |
| 检查清单逐项勾满 | A3 已较全，A1/A2 受阻 | 持续 |

---

## 5. 本机环境（恢复用）

### 路径

```text
仓库     C:\Users\13906\XiaomiMiMoProjects\CTF\app-privacy-audit
实验室   C:\Users\13906\privacy-lab\
  apks\   A1/A2/A3 APK（勿提交 Git）
  tools\  frida-server, jadx\, apktool.jar, frida-gadget-*.so, debug.keystore
  gadget-work\  A1/A2 反编译 + gadget 注入工作目录（勿提交）
  jadx-moji\  jadx-douban\   # 已反编译输出
  logs\   Frida/logcat 原始日志
SDK      c:\trae_solo\workspace\android-studio\android-sdk
AVD      privacy-api30  (Android 11, x86_64, google_apis)  # 仅 A3 可用
真机     小米 14 Ultra (24031PN0DC / d52606e6) arm64-v8a 无 root
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
cd C:\Users\13906\XiaomiMiMoProjects\CTF\app-privacy-audit
frida -U -p <pid> -l scripts\frida\all_hooks.js

# 注意
# - Frida 17 不要 --no-pause
# - Python API 在 spawn 后立刻 load 可能 Java undefined；CLI attach 更稳
# - A1 本 AVD 起不来；A2 attach 会自杀
# - 真机无 root：frida-server 无法 attach 商业 App；Gadget 重打包被壳杀
```

详见 `docs/environment.md`。

---

## 6. Git 提交脉络（master）

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

工作区当时干净；远程 `origin/master` 已同步。

---

## 7. 恢复工作建议顺序

1. `git pull`，确认 `master` 最新  
2. 启动 AVD + `frida-server`，用 A3 冒烟 `frida-ps -U`  
3. 按目标选一条线：  
   - **有 ARM 真机** → 重跑 A1/A2 动态，填 D-*  
   - **无真机** → 做 A3 或 A2 流量（mitmproxy）  
   - **写报告** → 补 04 流量 / 06 结论，或 A1/A2 政策对照  
4. 证据一律脱敏后进 `evidence/<pkg>/`，报告只引用编号  
5. 提交时说明「测了什么、没测什么」

---

## 8. 风险与约定（交接必读）

- 不提交 APK / 原始 PCAP / 未脱敏日志  
- 静态命中 ≠ 违规；动态未观测 ≠ 不存在  
- 受阻必须写清原因（ABI / 壳 / 反注入）  
- 法规条文引用前核对原文，不编条号  
- 研究仅限自有设备上的公开分发应用  

---

## 9. 联系上下文

- 竞赛通知联系人（仅背景，本项目不参赛）：许艳萍 17816124715 / 颜曰越 0571-86919137 / nisc@hdu.edu.cn  
- 官网：https://zjnisc.hdu.edu.cn/  
- 赛题原文：上级目录或 `assets/qiye-mingti.docx`（竞赛附件1，本地曾下载）

---

## 10. 下次开工检查清单

- [ ] `git status` 干净且 `origin` 同步  
- [ ] 模拟器/真机可 `adb devices`  
- [ ] `frida --version` 与设备端 server 一致  
- [ ] A3 能 attach 不自杀（环境健康探针）  
- [ ] 明确本轮只做一条线（动态复测 / 流量 / 政策 / 文档）  

— 交接完毕 —
