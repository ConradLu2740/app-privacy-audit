# E-A1-dyn-02 — 真机动态复测（Frida Gadget 重打包）

> 日期：2026-09-15  
> 设备：小米 14 Ultra（arm64-v8a），MIUI 生产版（`ro.debuggable=0`）  
> 结论：**受阻 — 壳完整性校验检测到重签名，进程被杀**

---

## 1. 尝试路径

无 root，`frida-server` 无法 attach 非 debuggable 商业 App。改走 **Frida Gadget 重打包**：

1. apktool 2.11.1 反编译 `A1-moji-V9.0942.02.apk`
2. 注入 `libfrida-gadget.so`（arm64 + armeabi-v7a）+ `libfrida-gadget.config.so`（listen `0.0.0.0:27042`）
3. 在壳 Application `s.h.e.l.l.S` 的 `attachBaseContext` / `onCreate` 插入 `System.loadLibrary("frida-gadget")`
4. apktool 回编 + debug keystore 重签名 + `adb install`

## 2. 观测

| 现象 | 细节 |
|------|------|
| 安装 | `INSTALL_FAILED_USER_RESTRICTED` → 开启 MIUI「USB 安装」后成功 |
| 启动 | `am start` 后进程存在，PID 不稳定（反复变化） |
| 端口 | `*:27042` 短暂 LISTEN，gadget 加载过 |
| 存活 | **进程反复死亡**：`ActivityManager: Process com.moji.mjweather has died: fg TOP` |
| 连接 | `frida-ps -H 127.0.0.1:27042` → `unable to connect to remote frida-server`（进程已死） |
| 壳 | Application = `s.h.e.l.l.S`（爱加密），`appComponentFactory=s.h.e.l.l.A` |
| 32 位 | 日志 `untrusted_app_32`，壳以 32 位加载 `libexec.so` |

## 3. 判定

爱加密壳在启动阶段做完整性校验（签名 / 文件哈希），检测到重打包后主动杀进程。  
**静态命中结论不受影响**；动态 D-* 在无 root / 无壳脱壳前提下仍无法观测。

## 4. 可行后续（按成本）

1. **解锁 Bootloader + Magisk root** → frida-server attach 原版 APK（一劳永逸，清数据）
2. 脱壳后 patch 壳校验（成本高，超出作品集范围）
3. 仅用静态 + 政策对照完成 A1（当前策略）

## 5. 工件

- 反编译目录：`<lab>\gadget-work\A1-decompiled\`
- gadget APK：`<lab>\gadget-work\A1-gadget.apk`（未入库）
- frida-gadget：17.18.0 android-arm / android-arm64
