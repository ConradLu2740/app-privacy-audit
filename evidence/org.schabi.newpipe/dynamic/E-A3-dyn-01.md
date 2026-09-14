# E-A3-dyn-01 · Frida 注入成功（对照样本）

- **结论一句话：** NewPipe 0.29.1 在 x86_64 AVD 上可启动，Frida attach 后 `all_hooks.js` 安装成功且进程存活；观测窗口内**未**触发设备标识/定位 Hook（与开源低采集定位一致）。
- **样本：** A3 / org.schabi.newpipe / 0.29.1 (1015)
- **步骤：**
  1. `pm clear` + `am start .MainActivity`
  2. 立即 `frida -U -p <pid> -l scripts/frida/all_hooks.js`
  3. 轻量 UI：点击/滑动约 20s
  4. 确认 `pidof` 仍存活
- **关键输出：**
  ```
  [HOOK][all] combined hooks ready
  （无 getDeviceId / getLastKnownLocation 等业务命中）
  pid still 8449
  ```
- **原始脱敏日志：** `E-A3-dyn-01.log`
- **关联检查项：** D-01…D-06 工具链验证；D-* 业务命中=`未观测到`（窗口内）
- **采集时间：** 2026-09-14
- **意义：** 证明同环境动态链路可用；与 A1/A2 受阻形成对照
