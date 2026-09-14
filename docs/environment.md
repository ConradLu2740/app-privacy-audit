# 测试环境说明

> 记录你实际使用的版本。他人复现时以本文件 + 样本元数据为准。

## 1. 主机

| 项 | 值 |
|----|----|
| OS | Windows（示例，按实际填写） |
| 架构 | x86_64 |
| 日期 | |

## 2. 模拟器 / 设备

| 项 | 值 |
|----|----|
| 模拟器 | （如 MuMu / 夜神 / 雷电 / Android Studio AVD） |
| Android 版本 | （建议 9–11） |
| 是否 Root | |
| 网络 | 主机代理 / 桥接 |

## 3. 静态工具

| 工具 | 版本 | 用途 |
|------|------|------|
| Jadx-gui | | 反编译浏览 |
| apktool（可选） | | 资源/Manifest |
| aapt（可选） | | 权限与包信息 |

## 4. 动态工具

| 工具 | 版本 | 用途 |
|------|------|------|
| Frida (client) | | Hook |
| frida-server | 与 client **同版本** | 设备端 |
| objection（可选） | | SSL unpin / 辅助 |

### Frida 冒烟步骤

```bash
# 1) 确认设备
adb devices

# 2) 推送并启动 frida-server（版本需匹配）
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c '/data/local/tmp/frida-server &'"   # 或模拟器 root 方式

# 3) 列进程 / 附加
frida-ps -U
frida -U -f <package.name> -l scripts/frida/all_hooks.js --no-pause
```

若 spawn 不稳，可先启动 App 再：

```bash
frida -U -n <AppLabel> -l scripts/frida/all_hooks.js
```

## 5. 流量工具

| 工具 | 配置要点 |
|------|----------|
| mitmproxy / Charles | 模拟器 Wi‑Fi 代理指向主机；安装并信任用户证书 |
| PCAPdroid（备选） | 设备侧抓包，适合 HTTPS 不解密时看 SNI/明文 HTTP |

**注意：** Android 7+ 应用默认不信任用户 CA。可选路径：

1. 使用可配置的模拟器镜像  
2. 用 objection / 脚本做 SSL unpinning（写入实际步骤）  
3. 失败则如实写局限，优先抓明文 HTTP  

## 6. 样本安装

- 从**官方应用商店或官网**自行下载 APK  
- 计算哈希后填入报告样本表  
- **禁止**把 APK 提交进 Git  

```bash
# 示例
Get-FileHash .\sample.apk -Algorithm SHA256
```

## 7. 数据与脱敏

见 [../evidence/README.md](../evidence/README.md)。原始 PCAP / 完整日志仅本地保留。
