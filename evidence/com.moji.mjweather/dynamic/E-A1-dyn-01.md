# E-A1-dyn-01 · 冷启动动态受阻（ABI + 爱加密壳）

- **结论一句话：** 墨迹天气 9.0942.02 在 x86_64 AVD 上无法完成冷启动，动态 Hook 无法开展。
- **样本：** A1 / com.moji.mjweather / 9.0942.02
- **步骤：**
  1. `pm clear com.moji.mjweather`
  2. `frida -U -f com.moji.mjweather -l all_hooks.js` → 应用崩溃
  3. 无 Frida 直接 `am start` → **同样崩溃**（排除「仅 Frida 导致」）
  4. 检查 APK：`lib/` 仅有 `arm64-v8a`、`armeabi-v7a`
- **关键日志（脱敏摘录）：**
  ```
  E AndroidRuntime: java.lang.UnsatisfiedLinkError: No implementation found for
    java.lang.ClassLoader s.h.e.l.l.N.al(...)
  at s.h.e.l.l.A.instantiateApplication
  Process: com.moji.mjweather
  ```
- **关联假设：** H-01…H-06 未验证
- **关联检查项：** D-*
- **采集时间：** 2026-09-14
- **处置：** 状态=`受阻`；需 ARM 真机/ARM 镜像后复测
