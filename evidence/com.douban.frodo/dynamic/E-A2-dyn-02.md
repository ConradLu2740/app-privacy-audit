# E-A2-dyn-02 — 真机动态复测（Frida Gadget 路径评估）

> 日期：2026-09-15  
> 设备：小米 14 Ultra（arm64-v8a，无 root）  
> 结论：**未完整执行 — 壳为网易易盾，与 A1 同类风险；本轮优先验证 A1 后记录**

---

## 1. 背景

A2 豆瓣此前在 x86 AVD 上可启动，但 `frida attach` 后进程自杀（疑似反注入）。  
真机无 root，计划同 A1 走 Gadget 重打包。

## 2. 静态确认

- Application = `com.netease.nis.wrapper.MyApplication`（**网易易盾 NIS 加固**）
- 大量 `native` 混淆方法（`n0110…` / `n1110…`），壳逻辑在 native 层
- 与 A1 爱加密同属商业加固，重签名触发完整性校验风险高

## 3. 本轮状态

- 已 apktool 反编译：`<lab>\gadget-work\A2-decompiled\`
- **未注入 gadget / 未重打包安装**（A1 先验证失败后，避免重复无效劳动）
- 原版 APK 仍可安装启动（此前 E-A2-dyn-01）

## 4. 判定

在无 root 前提下，A2 动态与 A1 同等受阻。  
解锁 Bootloader + root 后，可对**原版 APK** 直接 `frida-server attach`，无需重打包。

## 5. 后续

优先 root 路径；root 后 A1/A2 一并复测 D-*。
