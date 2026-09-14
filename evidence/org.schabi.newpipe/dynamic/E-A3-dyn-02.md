# E-A3-dyn-02 · 标准化动态剧本（完整）

- **结论一句话：** 冷启动 + 底部 Tab 切换 + 列表滚动 + 进入条目约 30s，进程全程存活；`all_hooks.js` 全程在线，**未观测到**设备标识/定位/剪贴板/应用列表类 API 调用。
- **样本：** A3 / org.schabi.newpipe / 0.29.1 (1015)
- **环境：** AVD privacy-api30 · Frida 17.18.0 · 2026-09-14
- **步骤：**
  1. `pm clear` → `am start .MainActivity`（COLD，TotalTime≈1.1s）
  2. 0.8s 后 `frida -U -p <pid> -l all_hooks.js`
  3. 剧本：tap 居中 / back / 三 Tab / 滚动 / 点条目 / 再 back / 再滚动
  4. 结束时 `pidof` 仍为同一 PID
- **关键输出：**
  ```
  combined hooks ready
  （无业务 -> 命中行）
  alive_pid=9083
  ```
- **原始日志：** `E-A3-dyn-02.log`
- **关联假设：** 低采集基线 — 窗口内 D-01/02/03/05/09/10 = `未观测到`
- **局限：** 未覆盖登录后路径、后台长时间、自定义服务端配置；「未观测到」≠ 全版本不可能
- **采集时间：** 2026-09-14
