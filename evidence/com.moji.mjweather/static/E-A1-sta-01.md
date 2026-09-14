# E-A1-sta-01 · 权限与敏感 API 静态汇总

- **结论一句话：** 墨迹天气声明精确定位+后台定位+活动识别等扩展权限，Jadx 全树可见大量设备标识与 OAID 相关调用线索。
- **样本：** A1 / com.moji.mjweather / 9.0942.02
- **步骤：**
  1. `aapt dump permissions A1-moji-V9.0942.02.apk`
  2. Jadx 反编译至 `jadx-moji/sources`，`rg` 统计敏感 API 文件数
- **关键摘录（已脱敏/摘要）：** 见 `docs/report/02-static-analysis.md` §A1
- **关联检查项：** S-01 S-10 S-12 S-20
- **采集时间：** 2026-09-14
- **局限：** 静态命中 ≠ 运行时必然调用；以动态证据为准
