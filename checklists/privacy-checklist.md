# Android App 隐私检查清单 v1（执行记录）

> 每个样本使用**同一清单**，保证横向可比。  
> 结论写入报告时必须挂证据编号（见 [evidence/README.md](../evidence/README.md)）。  
> 状态：`未测` / `未观测到` / `观测到` / `不适用` / `受阻`（写明原因）。  
> 本版本：2026-09-17 全部条目按 A1/A2/A3 三样本勾完；S/D/T/C 与 02/03/04/05 章节、证据 `E-<pkg>-<line>-nn` 一一对应。

---

## 0. 样本元数据

| 字段 | A1 墨迹天气 | A2 豆瓣 | A3 NewPipe |
|------|------------|--------|-----------|
| 应用名 | 墨迹天气 | 豆瓣 | NewPipe |
| 包名 | `com.moji.mjweather` | `com.douban.frodo` | `org.schabi.newpipe` |
| versionName / versionCode | 9.0942.02 / 1009094202 | 7.133.0 / 361 | 0.29.1 / 1015 |
| 下载渠道与日期 | 官网 `apps.mojicdn.com`，2026-09-14 | 官网 `andariel.douban.com`，2026-09-14 | F-Droid，2026-09-14 |
| APK SHA-256 | `62DD0E3A…090DB7` | `0DB1996A…FDA9FDF` | `1D66D19E…1A84B7E8` |
| 测试环境 | 小米 14 Ultra（arm64-v8a，无 root） | 同左 | AVD `privacy-api30`（Android 11, x86_64, google_apis） |
| 测试人 / 日期 | ConradLu / 2026-09-14~17 | ConradLu / 2026-09-14~17 | ConradLu / 2026-09-14~17 |

---

## 1. 静态：Manifest 与权限

| ID | 检查项 | A1 状态 | A1 证据 | A2 状态 | A2 证据 | A3 状态 | A3 证据 |
|----|--------|---------|---------|---------|---------|---------|---------|
| S-01 | `uses-permission` 全量列表 | 已列 | E-A1-sta-01 | 已列 | E-A2-sta-01 | 已列 | E-A3-sta-01 |
| S-02 | 危险权限与功能匹配 | 已审 | E-A1-sta-01 | 已审 | E-A2-sta-01 | 不适用 | E-A3-sta-01 |
| S-03 | `READ_PHONE_STATE` / 设备标识相关 | 未声明（代码层仍有 API） | E-A1-sta-01 | 未声明（代码层仍有 API） | E-A2-sta-01 | 未声明 | E-A3-sta-01 |
| S-04 | `ACCESS_FINE_LOCATION` + `COARSE` | 双声明 | E-A1-sta-01 | 双声明 | E-A2-sta-01 | 未声明 | E-A3-sta-01 |
| S-05 | `READ_CONTACTS` | 未声明（API 线索 3 处） | E-A1-sta-01 | 未声明 | E-A2-sta-01 | 未声明 | E-A3-sta-01 |
| S-06 | 剪贴板（静态仅线索） | `ClipboardManager` 8 文件；`getPrimaryClip` 1 | E-A1-sta-01 | `ClipboardManager` 30 文件；`getPrimaryClip` 6 | E-A2-sta-01 | 未见 | E-A3-sta-01 |
| S-07 | 旧外部存储权限 | 声明（`READ/WRITE_EXTERNAL_STORAGE`） | E-A1-sta-01 | 声明 | E-A2-sta-01 | 仅 `WRITE_EXTERNAL_STORAGE` | E-A3-sta-01 |
| S-08 | 导出组件保护 | 见 02 章（S-08） | E-A1-sta-01 | 见 02 章（S-08） | E-A2-sta-01 | 不适用 | E-A3-sta-01 |
| S-09 | `QUERY_ALL_PACKAGES` / 大范围可见性 | 未声明；`PACKAGE_USAGE_STATS`（maxSdk 28） | E-A1-sta-01 | **已声明** | E-A2-sta-01 | 未声明 | E-A3-sta-01 |

## 2. 静态：代码与 SDK 线索

| ID | 检查项 | A1 状态（命中文件数） | A2 状态（命中文件数） | A3 状态 |
|----|--------|---------------------|---------------------|---------|
| S-10 | 设备标识 API | `getDeviceId` 44；`getImei` 18；`getMeid` 4；`getSubscriberId` 5；`getSimSerialNumber` 3；`ANDROID_ID` 9 | `getDeviceId` 53；`getImei` 23；`getMeid` 2；`getSubscriberId` 7；`ANDROID_ID` 2 | 未见 |
| S-11 | MAC | `getMacAddress` 29 | `getMacAddress` 24 | 未见 |
| S-12 | 定位 API | `getLastKnownLocation` 7；`requestLocationUpdates` 4 | 7 / 9 | 未见 |
| S-13 | 通讯录 | `ContactsContract` 3 | 未见 | 未见 |
| S-14 | 短信/通话 | 未见 | 未见 | 未见 |
| S-15 | 剪贴板 | `ClipboardManager` 8；`getPrimaryClip` 1 | `ClipboardManager` 30；`getPrimaryClip` 6 | 未见 |
| S-16 | 传感器 | 存在（活动识别步骤） | 存在（加速度/陀螺仪） | 存在（系统支持） |
| S-17 | 已安装应用列表 | 未直接命中（依赖 `PACKAGE_USAGE_STATS`） | `QUERY_ALL_PACKAGES` 已声明 + `queryIntentActivities` 命中 | 未见 |
| S-18 | 明文存储线索 | 未见 `MODE_WORLD_READABLE`；无加密 SQLite 命中 | 同 A1 | N/A（开源） |
| S-19 | 明文 HTTP | `http://` 字符串 86（多文档/常量） | 93 | 未见 |
| S-20 | 第三方 SDK 包名 | 友盟 / 个推 / 穿山甲 / 高德 / 百度 / 腾讯 / OAID 簇（com.zui.deviceids 等） | 友盟 / 穿山甲 / 阿里 mtop / 高德 / 京东 / 腾讯 / 厂商推送 | 未见商业 SDK |
| S-21 | WebView JS 桥 | `addJavascriptInterface` 16 | 20 | 未见 |
| S-22 | 日志泄露 | 见 02 章；`Log.d/v` 命中 | 见 02 章 | 未见 |

> OAID 命中（A1）：**323** 文件。OAID 命中（A2）：143 文件。详见 02 章 §A1 §A2。

**静态产出：** 假设列表 H-01…H-15（见 `docs/report/02-static-analysis.md`）。

---

## 3. 动态：运行时行为（Frida）

> 脚本见 `scripts/frida/`。窗口：冷启动 + ~30s 剧本（A3）/ 60s 前台（A2，未登录）/ A1 全部受阻。

| ID | 检查项 | A1 状态 | A1 证据 | A2 状态 | A2 证据 | A3 状态 | A3 证据 |
|----|--------|---------|---------|---------|---------|---------|---------|
| D-01 | IMEI/MEID/DeviceId | **受阻**（ARM-only AVD 起不来 + 真机无 root + Gadget 重打包壳杀进程） | E-A1-dyn-01/02 | **受阻**（疑似反 Frida：attach 后进程自杀；壳 = 网易易盾 NIS） | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-02 | Android ID | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-03 | SubscriberId / SIM | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-04 | MAC | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到（Android 10+ 占位） | E-A3-dyn-02 |
| D-05 | 精确定位 | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-06 | 粗略定位 | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-07 | 通讯录读取 | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-08 | 短信/通话记录 | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-09 | 剪贴板读取 | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-10 | 已安装应用列表 | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-11 | 相机/麦克风打开 | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 未观测到 | E-A3-dyn-02 |
| D-12 | 网络请求伴随敏感字段 | 同上 | E-A1-dyn-01/02 | 同上 | E-A2-dyn-01/02 | 流量线交叉：仅 `www.youtube.com` | E-A3-dyn-02 · E-A3-trf-01 |

**动态产出：** 证据 `E-<pkg>-dyn-01/02`，含时间戳、进程、调用栈摘要。

**受阻说明：**
- A1 真机为小米 14 Ultra（arm64-v8a），无 root；x86_64 AVD 上 APK 启动即崩（仅 ARM）。尝试 Gadget 重打包 → 重签名后壳校验杀进程。详见 `evidence/com.moji.mjweather/dynamic/E-A1-dyn-02.md`。
- A2 attach 后进程自杀，未捕获到任何 Frida 调用栈。怀疑网易易盾 NIS 反注入；x86_64 AVD 未尝试（AVD 仅 A3 用）。详见 `evidence/com.douban.frodo/dynamic/E-A2-dyn-01.md`。

---

## 4. 流量：传输与明文

> 工具：PCAPdroid 1.8.6（Android VPN，**连接级**，无载荷解密）。窗口：A2 60s 冷启动 + 首页；A3 30s 冷启动 + 搜索。

| ID | 检查项 | A1 状态 | A1 证据 | A2 状态 | A2 证据 | A3 状态 | A3 证据 |
|----|--------|---------|---------|---------|---------|---------|---------|
| T-01 | 纯 HTTP 明文请求 | **命中**：50 条明文 HTTP，多为自有日志/CDN 端点（`v1.log.moji.com` 等）及 `voiceads.cn`、穿山甲打包域名 | E-A1-trf-02 | 仅观察连接级；无明文 HTTP 命中（仅 TLS） | E-A2-trf-01 | 仅 `www.youtube.com`（TLS/DNS） | E-A3-trf-01 |
| T-02 | HTTPS 体中敏感字段 | 未解（无 root + 用户 CA 不被信任） | E-A1-trf-02 | 未解 | E-A2-trf-01 | 未解 | E-A3-trf-01 |
| T-03 | 敏感字段是否与政策一致 | 部分：第三方 SDK 已观测联网（京东/GDT/穿山甲/高德/百度/个推/友盟），与政策第三方清单核对待细做 | E-A1-trf-02 · E-A1-pol-01 | 「自有域名」与「安全运行」一致 | E-A2-trf-01 · E-A2-pol-01 | 「仅 YouTube 官方」与 GDPR 政策一致 | E-A3-trf-01 · E-A3-pol-01 |
| T-04 | 是否向非政策列出的第三方域名发送 | **观测到大量第三方域名**（约 45% 连接，见 E-A1-trf-02 §3 分组表） | E-A1-trf-02 | **未观测到第三方域名**（60s 未登录） | E-A2-trf-01 | **未观测到第三方追踪域名** | E-A3-trf-01 |
| T-05 | 证书校验/固定 | 未做（连接级元数据） | E-A1-trf-02 | 未做（连接级元数据） | E-A2-trf-01 | 未做 | E-A3-trf-01 |
| T-06 | 本地明文落盘后再上传 | 未做 | E-A1-trf-02 | 未做 | E-A2-trf-01 | 未做 | E-A3-trf-01 |

**流量产出：** 过滤条件（host/关键字）+ 脱敏摘录，**不要提交原始 PCAP**。

---

## 5. 隐私政策与合规对照

> 详细方法见 [../docs/compliance.md](../docs/compliance.md)。三列对照详见 [../docs/report/05-compliance-review.md](../docs/report/05-compliance-review.md)。

| ID | 检查项 | A1 状态 | A1 证据/条款 | A2 状态 | A2 证据/条款 | A3 状态 | A3 证据/条款 |
|----|--------|---------|-------------|---------|-------------|---------|-------------|
| C-01 | 政策是否可从 App 内触达 | 受阻（首启卡 splash 未实测），HTML5 页可公开访问 | E-A1-pol-01 | 可（应用内有入口 + 官网） | E-A2-pol-01 | 仅官网/未截屏 App 内路径 | E-A3-pol-01 |
| C-02 | 收集的个人信息类型是否列全 | 列全（IMEI/MEID/IMSI/OAID/Android_ID/MAC/IDFA/GUID） | E-A1-pol-01 (C-02…C-04-m) | 列全（Android ID/OAID/GUID） | E-A2-pol-01 | 列全（仅邮箱/崩溃字段） | E-A3-pol-01 (C-04/C-05-a) |
| C-03 | 收集目的是否明确 | 明确（场景化表格） | E-A1-pol-01 §1 | 明确 | E-A2-pol-01 §1 | 明确 | E-A3-pol-01 §1 |
| C-04 | 是否声明第三方 SDK/共享对象 | 部分点名（推啊、平安好医生）；友盟/穿山甲/高德/百度/腾讯 仅笼统表述 | E-A1-pol-01 (R-13) | 声明 + 提供《第三方合作清单》 | E-A2-pol-01 (R-24) | 声明「不向第三方共享」 | E-A3-pol-01 (C-06-a) |
| C-05 | 是否说明存储期限 | 抓取段未展开「7. 您个人信息的存储」具体期限 | E-A1-pol-01 §4 | 「实现目的所必需 + 法律法规要求」 | E-A2-pol-01 §1 | Sentry 备份「约 6 个月」 | E-A3-pol-01 (C-07-a) |
| C-06 | 用户权利入口 | 解析过的章节含「5. 您如何管理」 | E-A1-pol-01 §1 | 可在功能页面 + 客服 | E-A2-pol-01 §1 | GDPR Art.15-21 全列 | E-A3-pol-01 (C-08-a) |
| C-07 | 敏感权限（通讯录/短信/精确位置）显著说明 | 精确位置显著说明；通讯录/短信未声明 | E-A1-pol-01 (C-13-m) | 精确位置「仅签到」显著说明；通讯录/短信未声明 | E-A2-pol-01 §1 | 不涉及 | E-A3-pol-01 |
| C-08 | 启动前是否违规强制索权/先收后告知 | 动态受阻，未验证时序 | E-A1-pol-01 §2 | 动态受阻，未验证时序 | E-A2-pol-01 §4 | 动态未观测到索权 | E-A3-dyn-02 · E-A3-pol-01 |

---

## 6. 横向对比矩阵（已填）

| 检查项 | A1 墨迹 | A2 豆瓣 | A3 NewPipe |
|--------|---------|---------|------------|
| 设备标识收集 | 政策已披露 + 静态 SDK 信号强（OAID 323 文件），动态**受阻** | 政策已披露 + 自研 `deviceId` + OAID 143 文件，动态**受阻** | 静态无商业 SDK；动态**未观测到**；政策声明不收集 |
| 精确定位 | 政策已披露（与场景匹配）；后台定位；动态**受阻** | 政策已披露（**仅签到**）；动态**受阻** | 静态未声明；动态**未观测到**；政策不涉及 |
| 通讯录 | 静态未声明；API 线索 3 处（SDK 残留）；动态**受阻** | 静态未声明；动态**受阻** | 静态未声明；动态**未观测到** |
| 明文传输 | 流量**受阻**（首启卡 splash） | 连接级未发现明文 HTTP | 连接级未发现明文 HTTP；唯一 `www.youtube.com`（TLS） |
| 政策一致性 | 字段粒度细；第三方 SDK 部分点名；动态受限仅静态一致 | 字段 + 三附件齐全；商业 SDK 60s 未触发；动态受限仅静态一致 | 三线闭环一致：低采集设计与政策匹配 |
| 综合风险等级 | **中**（OAID 大 + 后台静默收集） | **低**（合规写法 + 流量仅自有域名） | **无/观察** |

---

## 执行进度（2026-09-17）

| 阶段 | A1 墨迹 | A2 豆瓣 | A3 NewPipe |
|------|---------|---------|------------|
| 元数据/哈希/锁样 | 完成 | 完成 | 完成 |
| S-* 静态 | 完成（E-A1-sta-01） | 完成（E-A2-sta-01） | 完成（E-A3-sta-01） |
| 假设 H-xx | 已建（H-01…H-06） | 已建（H-10…H-15） | 低采集基线 |
| D-* 动态 Hook | **受阻**（ARM-only + ijiami 壳） | **受阻**（网易易盾 NIS 反注入） | **完成**（E-A3-dyn-01/02，均未观测到） |
| T-* 流量 | **完成**（E-A1-trf-02，首启 60s 观测到 535 连接 / 74 主机，含 50 条明文 HTTP 与大量第三方 SDK 域名） | **完成**（E-A2-trf-01，60s 仅自有域名） | **完成**（E-A3-trf-01，仅 `www.youtube.com`） |
| C-* 政策对照 | **完成**（E-A1-pol-01，14 条 C-xx-m，仅静态层） | **完成**（E-A2-pol-01，三附件齐全，仅静态层） | **完成**（E-A3-pol-01，三线闭环） |

详细静态结论见 [../docs/report/02-static-analysis.md](../docs/report/02-static-analysis.md)；合规对照见 [../docs/report/05-compliance-review.md](../docs/report/05-compliance-review.md)；结论与修复建议见 [../docs/report/06-findings-and-fixes.md](../docs/report/06-findings-and-fixes.md)。

---

## 使用约定

1. **先静态后动态再流量**，减少盲测。  
2. 每条「观测到」必须能指向证据文件路径。  
3. 「未观测到」要写清操作路径与时间窗口。  
4. 受阻（加固、证书锁定失败等）写入局限章节，不编造结论。