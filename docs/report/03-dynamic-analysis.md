# 03 · 动态分析

> 对应清单 D-* 与假设 H-xx。脚本：`scripts/frida/`。  
> 测试日期：2026-09-14 · AVD `privacy-api30`（Android 11 x86_64）· Frida 17.18.0

## 测试操作路径（标准化）

1. `pm clear` 后冷启动  
2. 尝试 Frida 注入（spawn / attach）  
3. 观察 logcat 与 Hook 日志  

---

## A1 墨迹天气 — **动态受阻**

| 项 | 结果 |
|----|------|
| 能否在本模拟器启动 | **否**（无 Frida 也崩） |
| 崩溃点 | `s.h.e.l.l.N.al`（爱加密壳 `instantiateApplication`） |
| 异常 | `UnsatisfiedLinkError` |
| 根因分析 | APK 仅含 `arm64-v8a` / `armeabi-v7a` 原生库，**无 x86/x86_64**；本 AVD 为 x86_64，壳无法加载 |
| Frida spawn | 加剧/同样崩溃 |
| 结论 | **D-01… 全部无法在本环境观测**；静态假设 H-01… 保留，待 ARM 环境复测 |

**证据：** [../../evidence/com.moji.mjweather/dynamic/E-A1-dyn-01.md](../../evidence/com.moji.mjweather/dynamic/E-A1-dyn-01.md)

### 解除阻塞路径（后续）

1. 创建 **ARM 系统镜像 AVD**（慢，Windows 上通常无硬件加速）  
2. 使用支持 ARM 转译的模拟器（部分 MuMu/雷电版本）  
3. 真机（推荐）+ `frida-server` arm64  
4. 或更换无加固且带 x86_64 的天气类样本  

---

## A2 豆瓣 — **动态受阻（反注入）**

| 项 | 结果 |
|----|------|
| 无 Frida 启动 | **成功**（Splash 正常，进程存活） |
| ABI | 含 `x86_64`，兼容本 AVD |
| Frida spawn+resume | 进程可短时存活 |
| Frida attach（CLI `-p`） | Hook 安装成功后 **`Process terminated`** |
| 判断 | 疑似 **反 Frida / 反调试**：检测到注入后自杀 |
| 未观测到 | 不代表运行时不收集，只代表本注入路径失败 |

**证据：** [../../evidence/com.douban.frodo/dynamic/E-A2-dyn-01.md](../../evidence/com.douban.frodo/dynamic/E-A2-dyn-01.md)

### 解除阻塞路径（后续）

1. Frida 改名 + 隐藏端口 / `frida-gadget` 注入到重打包（成本高）  
2. 使用 Magisk + 隐藏、或商业加固对抗方案（超出本项目 YAGNI）  
3. **被动观测**：logcat、`dumpsys`、流量侧（mitmproxy，需处理 SSL pinning）  
4. 更换反注入较弱的对照样本，A2 作「静态 + 受阻说明」案例  

---

## 对照：动态链路在 A3 上可用

| 包名 | 结果 |
|------|------|
| `org.schabi.newpipe` (A3) | **成功**：attach 后 hooks 安装、进程存活；窗口内无 IMEI/定位命中 |
| `de.danoeh.antennapod` | **成功**：同样可注入存活（备用对照） |
| `com.simplemobiletools.calculator` | 成功（早期工具链冒烟） |

**A3 证据：** [../../evidence/org.schabi.newpipe/dynamic/E-A3-dyn-01.md](../../evidence/org.schabi.newpipe/dynamic/E-A3-dyn-01.md)

说明：本环境 **Frida 工具链可用**；A1/A2 受阻来自样本自身（ABI/壳/反注入），非脚本错误。

---

## 假设状态

| 假设 | 状态 |
|------|------|
| H-01…H-06（A1） | **未验证**（环境受阻） |
| H-10…H-15（A2） | **未验证**（反注入受阻） |
| D-* 清单项 | A1/A2 标 `受阻` |

---

## 方法层收获（可写入作品集）

1. **选样阶段就要测 ABI**：`lib/` 下无目标模拟器 ABI → 动态线直接作废。  
2. **壳样本先做无注入启动**：区分「环境不兼容」vs「Frida 导致崩溃」。  
3. **反注入是动态分析一等公民风险**：需在报告「局限」中明示，禁止用静态命中冒充运行时行为。  
4. 练手包证明链路后，再上正式样本，避免误判脚本问题。
