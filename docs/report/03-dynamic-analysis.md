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

## A3 NewPipe — **动态完成（低采集基线）**

| 项 | 结果 |
|----|------|
| 启动 | COLD 成功（≈1.1s） |
| ABI | 含 x86_64，无壳 |
| Frida attach | **成功**，hooks 在线 |
| 进程 | 剧本全程存活（同 PID） |
| 观测窗口 | 冷启动 + Tab×3 + 滚动×2 + 进条目 ≈ 30s |

### 标准化剧本 D-* 结果

| ID | 检查项 | 冷启动 | 用户操作后 | 证据 | 结论 |
|----|--------|--------|------------|------|------|
| D-01 | IMEI/DeviceId | 否 | 否 | E-A3-dyn-02 | **未观测到** |
| D-02 | ANDROID_ID | 否 | 否 | E-A3-dyn-02 | **未观测到** |
| D-03 | SubscriberId/SIM | 否 | 否 | E-A3-dyn-02 | **未观测到** |
| D-04 | MAC | 未单独高亮 | — | — | 与 D-01 同脚本窗口 |
| D-05 | 精确定位 | 否 | 否 | E-A3-dyn-02 | **未观测到** |
| D-06 | 粗略定位 | 否 | 否 | E-A3-dyn-02 | **未观测到** |
| D-07 | 通讯录 | 否 | 否 | E-A3-dyn-02 | **未观测到** |
| D-09 | 剪贴板读 | 否 | 否 | E-A3-dyn-02 | **未观测到** |
| D-10 | 已安装应用 | 否 | 否 | E-A3-dyn-02 | **未观测到** |
| D-11 | 相机/录音 | 否 | 否 | E-A3-dyn-02 | **未观测到** |

**证据：**

- [E-A3-dyn-01](../../evidence/org.schabi.newpipe/dynamic/E-A3-dyn-01.md) 早期 attach 成功  
- [E-A3-dyn-02](../../evidence/org.schabi.newpipe/dynamic/E-A3-dyn-02.md) 完整剧本  

**解读（对照 A1/A2）：**  
Manifest 无定位/电话/通讯录权限（见 E-A3-sta-01），与动态「未观测到」一致——静态权限面与运行时行为对齐，作为**低采集基线**。A1/A2 静态命中大量标识符 API，但因环境/反注入无法用动态证实，故报告中必须分开表述。

备用对照：`de.danoeh.antennapod` 同样可注入存活（未做完整剧本）。

---

## 假设状态

| 假设 | 状态 |
|------|------|
| H-01…H-06（A1） | **未验证**（环境受阻） |
| H-10…H-15（A2） | **未验证**（反注入受阻） |
| A3 低采集基线 | **支持**（D-* 窗口内未观测到） |

---

## 方法层收获（可写入作品集）

1. **选样阶段就要测 ABI**：`lib/` 下无目标模拟器 ABI → 动态线直接作废。  
2. **壳样本先做无注入启动**：区分「环境不兼容」vs「Frida 导致崩溃」。  
3. **反注入是动态分析一等公民风险**：需在报告「局限」中明示，禁止用静态命中冒充运行时行为。  
4. 练手包证明链路后，再上正式样本，避免误判脚本问题。
