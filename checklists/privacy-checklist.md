# Android App 隐私检查清单 v1

> 每个样本使用**同一清单**，保证横向可比。  
> 结论写入报告时必须挂证据编号（见 [evidence/README.md](../evidence/README.md)）。  
> 状态：`未测` / `未观测到` / `观测到` / `不适用` / `受阻`（写明原因）。

## 0. 样本元数据

| 字段 | 内容 |
|------|------|
| 样本 ID | A1 / A2 / A3 |
| 应用名 | |
| 包名 | |
| versionName / versionCode | |
| 下载渠道与日期 | |
| APK SHA-256 | |
| 测试环境（模拟器/系统版本） | |
| 测试人 / 日期 | |

---

## 1. 静态：Manifest 与权限

| ID | 检查项 | 期望/关注点 | 状态 | 证据 |
|----|--------|-------------|------|------|
| S-01 | `uses-permission` 全量列表 | 与功能是否匹配 | | |
| S-02 | 危险权限（位置/通讯录/短信/电话/存储/相机/麦克风等） | 是否超范围声明 | | |
| S-03 | `READ_PHONE_STATE` / 设备标识相关 | 是否声明、是否必要 | | |
| S-04 | 精确定位 `ACCESS_FINE_LOCATION` | 与粗略定位是否同时申请 | | |
| S-05 | 通讯录 `READ_CONTACTS` | 是否声明 | | |
| S-06 | 剪贴板相关（运行时更准，静态仅线索） | | | |
| S-07 | `requestLegacyExternalStorage` / 所有文件访问 | 存储范围 | | |
| S-08 | 导出组件（`exported=true` 且无权限保护） | 非直接隐私，可作辅助面 | | |
| S-09 | 是否存在 `QUERY_ALL_PACKAGES` 或大范围 package visibility | 应用列表相关 | | |

## 2. 静态：代码与 SDK 线索

| ID | 检查项 | 搜索/API 线索 | 状态 | 证据 |
|----|--------|---------------|------|------|
| S-10 | 设备标识 API | `getDeviceId` `getImei` `getMeid` `getSubscriberId` `getSimSerialNumber` `getAndroidId` `Settings.Secure.ANDROID_ID` | | |
| S-11 | MAC / Wi‑Fi 标识 | `getMacAddress` `WifiInfo` | | |
| S-12 | 定位 API | `getLastKnownLocation` `requestLocationUpdates` `LocationManager` `FusedLocationProvider` | | |
| S-13 | 通讯录 | `ContactsContract` `ContentUris` | | |
| S-14 | 短信/通话记录 | `Telephony.Sms` `CallLog` | | |
| S-15 | 剪贴板 | `ClipboardManager` `getPrimaryClip` | | |
| S-16 | 传感器/运动 | `SensorManager`（步数等） | | |
| S-17 | 已安装应用列表 | `getInstalledPackages` `queryIntentActivities` | | |
| S-18 | 明文存储线索 | `MODE_WORLD_READABLE` `SharedPreferences` 明文写敏感键 `SQLite` 无加密 | | |
| S-19 | 明文 HTTP | `http://` 字符串、未强制 HTTPS | | |
| S-20 | 第三方 SDK 包名 | 友盟/个推/极光/穿山甲/微信/支付宝/各大广告与统计 | | |
| S-21 | WebView JS 桥 | `addJavascriptInterface` 是否暴露敏感方法 | | |
| S-22 | 日志泄露 | `Log.d/v` 打印设备号、token、手机号 | | |

**静态产出：** 假设列表 `H-01…`（需动态验证的点）。

---

## 3. 动态：运行时行为（Frida）

> 脚本见 `scripts/frida/`。记录：是否在**冷启动**触发、是否需**用户操作**触发。

| ID | 检查项 | Hook 点（示例） | 冷启动 | 用户操作后 | 证据 |
|----|--------|-----------------|--------|------------|------|
| D-01 | IMEI/MEID/DeviceId | `TelephonyManager.getDeviceId/getImei/getMeid` | | | |
| D-02 | Android ID | `Settings.Secure.getString` + `ANDROID_ID` | | | |
| D-03 | SubscriberId / SIM 序列号 | `getSubscriberId` `getSimSerialNumber` | | | |
| D-04 | MAC 地址 | `WifiInfo.getMacAddress` / 相关 | | | |
| D-05 | 精确定位 | `Location.getLatitude/getLongitude` `getLastKnownLocation` | | | |
| D-06 | 粗略定位 | Network/Cell 定位路径 | | | |
| D-07 | 通讯录读取 | `ContentResolver.query` + Contacts URI | | | |
| D-08 | 短信/通话记录 | 对应 ContentProvider query | | | |
| D-09 | 剪贴板读取 | `ClipboardManager.getPrimaryClip/getPrimaryClipDescription` | | | |
| D-10 | 已安装应用列表 | `PackageManager.getInstalledPackages` | | | |
| D-11 | 相机/麦克风打开 | `Camera.open` `AudioRecord.startRecording` | | | |
| D-12 | 网络请求伴随敏感字段 | 与流量线交叉验证 | | | |

**动态产出：** 证据 `E-<app>-dyn-nn`，含时间戳、进程、调用栈摘要。

---

## 4. 流量：传输与明文

| ID | 检查项 | 关注点 | 状态 | 证据 |
|----|--------|--------|------|------|
| T-01 | 是否存在纯 HTTP 明文请求 | `http://` 主机 | | |
| T-02 | HTTPS 体中是否可解出敏感字段 | 设备号、位置、手机号、token 明文 JSON/form | | |
| T-03 | 敏感字段是否与隐私政策声明的目的/第三方一致 | 对照 C-xx | | |
| T-04 | 是否向非政策列出的第三方域名发送 | 主机名单 | | |
| T-05 | 证书校验/固定情况（仅记录，不强制绕过叙事） | | | |
| T-06 | 本地明文落盘后再上传的路径（可选） | | | |

**流量产出：** 过滤条件（host/关键字）+ 脱敏摘录，**不要提交原始 PCAP**。

---

## 5. 隐私政策与合规对照

> 详细方法见 [../docs/compliance.md](../docs/compliance.md)。

| ID | 检查项 | 状态 | 证据/条款 |
|----|--------|------|-----------|
| C-01 | 政策是否可从 App 内触达 | | |
| C-02 | 收集的个人信息类型是否列全（对照静态/动态） | | |
| C-03 | 收集目的是否明确 | | |
| C-04 | 是否声明第三方 SDK/共享对象 | | |
| C-05 | 是否说明存储期限 | | |
| C-06 | 用户权利（查询/更正/删除/注销）入口是否可用 | | |
| C-07 | 敏感权限（通讯录/短信/精确位置）是否在政策中显著说明 | | |
| C-08 | 启动前是否违规强制索权/先收后告知（结合动态时序） | | |

---

## 6. 横向对比矩阵（多样本时填写）

| 检查项 | A1 | A2 | A3 |
|--------|----|----|-----|
| 设备标识收集 | | | |
| 精确定位 | | | |
| 通讯录 | | | |
| 明文传输 | | | |
| 政策一致性 | | | |
| 综合风险等级 | | | |

---

## 执行进度（2026-09-14）

| 阶段 | A1 墨迹 | A2 豆瓣 | A3 NewPipe |
|------|---------|---------|------------|
| 元数据/哈希/锁样 | 已完成 | 已完成 | 已完成 |
| S-* 静态 | 已完成 | 已完成 | 已完成（E-A3-sta-01） |
| 假设 H-xx | 已建 | 已建 | 低采集基线 |
| D-* 动态 Hook | **受阻** | **受阻** | **完成**（E-A3-dyn-01/02，均未观测到） |
| T-* 流量 | 未做 | 未做 | 未做（可选） |
| C-* 政策对照 | 未做 | 未做 | **完成**（E-A3-pol-01 / 报告 05） |

详细静态结论见 [../docs/report/02-static-analysis.md](../docs/report/02-static-analysis.md)。

---

## 使用约定

1. **先静态后动态再流量**，减少盲测。  
2. 每条「观测到」必须能指向证据文件路径。  
3. 「未观测到」要写清操作路径与时间窗口。  
4. 受阻（加固、证书锁定失败等）写入局限章节，不编造结论。
