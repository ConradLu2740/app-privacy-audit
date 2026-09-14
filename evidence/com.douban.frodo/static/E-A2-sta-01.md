# E-A2-sta-01 · 权限与敏感 API 静态汇总

- **结论一句话：** 豆瓣声明定位/相机/录音及 `QUERY_ALL_PACKAGES`，存在自研 deviceId 抽象与较多剪贴板相关代码。
- **样本：** A2 / com.douban.frodo / 7.133.0
- **步骤：**
  1. `aapt dump permissions A2-douban.apk`
  2. Jadx 反编译至 `jadx-douban/sources`，`rg` 统计；抽查 `com.douban.push` 等业务包
- **关键摘录：** 见 `docs/report/02-static-analysis.md` §A2  
  业务示例：`com.douban.push.internal.Settings.getDeviceId()`
- **关联检查项：** S-01 S-09 S-10 S-15 S-20
- **采集时间：** 2026-09-14
- **局限：** 自研 deviceId 生成逻辑需动态/流量确认，不可直接等同 IMEI
