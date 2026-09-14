# 测试环境说明

> 记录你实际使用的版本。他人复现时以本文件 + 样本元数据为准。  
> **本机已配好（2026-09-14）**，见下表；样本 APK 仍需自行下载。

## 1. 主机

| 项 | 值 |
|----|----|
| OS | Windows 10.0.26200 |
| 架构 | x86_64 |
| 日期 | 2026-09-14 |

## 2. 模拟器 / 设备

| 项 | 值 |
|----|----|
| 模拟器 | Android SDK Emulator |
| AVD 名 | `privacy-api30`（Pixel 4, API 30 google_apis x86_64） |
| Android 版本 | **11**（API 30） |
| 启动命令 | 见下方「启动模拟器」 |
| 是否 Root | `adb root` 可用（google_apis 镜像） |
| SDK 路径 | `c:\trae_solo\workspace\android-studio\android-sdk` |
| 实验室目录 | `C:\Users\13906\privacy-lab\` |

### 启动模拟器

```powershell
& "c:\trae_solo\workspace\android-studio\android-sdk\emulator\emulator.exe" `
  -avd privacy-api30 -no-snapshot-save -no-boot-anim -gpu swiftshader_indirect

# 等待启动完成
adb wait-for-device
adb shell getprop sys.boot_completed   # 应输出 1
```

## 3. 静态工具

| 工具 | 版本 | 路径 / 用途 |
|------|------|-------------|
| Jadx CLI | **1.5.1** | `C:\Users\13906\privacy-lab\tools\jadx\bin\jadx.bat` |
| aapt | build-tools 34/35 | SDK `build-tools` |
| Java | Android Studio JBR | `C:\Program Files\Android\Android Studio\jbr` |

```powershell
# Jadx 反编译到目录
& "C:\Users\13906\privacy-lab\tools\jadx\bin\jadx.bat" -d out\sample sample.apk
```

## 4. 动态工具

| 工具 | 版本 | 说明 |
|------|------|------|
| Frida (client) | **17.18.0** | `pip install frida-tools`（Python 3.11） |
| frida-server | **17.18.0** android-x86_64 | 已推到设备：`/data/local/tmp/frida-server` |
| adb | 37.0.0 | `c:\trae_solo\workspace\android-studio\android-sdk\platform-tools\adb.exe` |

### Frida 冒烟（已通过）

```powershell
adb root
adb shell "/data/local/tmp/frida-server -D &"
frida-ps -U

# Frida 17 默认 spawn 后自动恢复，无需 --no-pause
frida -U -f com.simplemobiletools.calculator -l scripts\frida\all_hooks.js
```

**注意：** Frida 17 已移除 `--no-pause`；若要暂停主线程用 `--pause`。

## 5. 流量工具

| 工具 | 配置要点 | 状态 |
|------|----------|------|
| mitmproxy / Charles | 模拟器 Wi‑Fi 代理 → 主机；安装用户 CA | 未配置（W4） |
| PCAPdroid | 设备侧抓包 | 备选 |

Android 7+ 默认不信任用户 CA。可选：可配置镜像 / SSL unpinning / 如实写局限。

## 6. 样本安装

- 从**官方应用商店或官网**自行下载 APK，放入 `C:\Users\13906\privacy-lab\apks\`  
- **禁止**把 APK 提交进 Git  

```powershell
Get-FileHash .\sample.apk -Algorithm SHA256
adb install -r .\sample.apk
```

### 当前实验室已装

| 包名 | 版本 | 来源 | 用途 |
|------|------|------|------|
| `com.moji.mjweather` | 9.0942.02 | 官网 CDN | **正式样本 A1** |
| `com.douban.frodo` | 7.133.0 | 官网下载 | **正式样本 A2** |
| `com.simplemobiletools.calculator` | — | F-Droid | Frida 冒烟（已通过） |

正式样本哈希与渠道见 [report/01-samples.md](report/01-samples.md)。

## 7. 数据与脱敏

见 [../evidence/README.md](../evidence/README.md)。原始 PCAP / 完整日志仅本地保留。

## 8. 工具路径速查

```powershell
$SDK  = "c:\trae_solo\workspace\android-studio\android-sdk"
$LAB  = "C:\Users\13906\privacy-lab"
$ADB  = "$SDK\platform-tools\adb.exe"
$EMU  = "$SDK\emulator\emulator.exe"
$JADX = "$LAB\tools\jadx\bin\jadx.bat"
$FS   = "$LAB\tools\frida-server"
```
