# E-A2-dyn-01 · 动态注入受阻（疑似反 Frida）

- **结论一句话：** 豆瓣 7.133.0 可正常启动，但 Frida attach 后进程立即死亡，疑似反注入自杀。
- **样本：** A2 / com.douban.frodo / 7.133.0
- **步骤：**
  1. 无注入 `am start` → Splash 正常，`pidof` 存活
  2. `frida -U -p <pid> -l all_hooks.js`
  3. 日志出现 `combined hooks ready` 后立刻 `Process terminated`
  4. logcat：`Process com.douban.frodo ... has died`
- **关键现象：**
  ```
  [HOOK][all] combined hooks ready
  [Android Emulator 5554::PID::7280]-> Process terminated
  ```
- **对照：** 同环境 `com.simplemobiletools.calculator` 注入成功 → 非工具链问题
- **关联假设：** H-10…H-15 未验证
- **关联检查项：** D-*
- **采集时间：** 2026-09-14
- **处置：** 状态=`受阻`；后续可尝试隐藏注入/被动流量，或换对照样本
