# E-A3-sta-01 · 权限静态汇总（开源对照）

- **结论一句话：** NewPipe 0.29.1 Manifest **未**声明定位、电话状态、通讯录等危险隐私权限，权限面显著小于 A1/A2。
- **样本：** A3 / org.schabi.newpipe / 0.29.1 (1015)
- **步骤：** `aapt dump permissions A3-newpipe-1015.apk`
- **声明权限（完整）：**
  - `INTERNET` / `ACCESS_NETWORK_STATE` / `WAKE_LOCK`
  - `WRITE_EXTERNAL_STORAGE`（下载媒体）
  - `SYSTEM_ALERT_WINDOW` / `FOREGROUND_SERVICE*` / `POST_NOTIFICATIONS` / `RECEIVE_BOOT_COMPLETED`
- **未声明（对照 A1/A2）：** `ACCESS_FINE/COARSE_LOCATION`、`READ_PHONE_STATE`、`READ_CONTACTS`、`QUERY_ALL_PACKAGES`、广告/厂商 OAID 权限簇
- **关联检查项：** S-01 S-02 S-03 S-04 S-05 S-09
- **采集时间：** 2026-09-14
