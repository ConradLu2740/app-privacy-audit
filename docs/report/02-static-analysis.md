# 02 · 静态分析

> 对应清单 S-*。样本元数据见 [01-samples.md](01-samples.md)。  
> 分析日期：2026-09-14 · 工具：aapt 35.0.0 + Jadx 1.5.1  
> 反编译输出（本地，不入 Git）：`C:\Users\13906\privacy-lab\jadx-moji\`、`jadx-douban\`

---

## A1 墨迹天气（`com.moji.mjweather` 9.0942.02）

### 2.1 权限（Manifest，危险/敏感摘录）

| 权限 | 类型 | 与功能相关？ | 观察 |
|------|------|--------------|------|
| `ACCESS_FINE_LOCATION` | 危险 | 是（天气核心） | 合理 |
| `ACCESS_COARSE_LOCATION` | 危险 | 是 | 与精确同时申请 |
| `ACCESS_BACKGROUND_LOCATION` | 危险 | 部分（后台天气推送） | 需政策显著说明；动态看是否滥用 |
| `ACTIVITY_RECOGNITION` | 危险 | 弱相关 | 值得对照政策「运动/健康」类描述 |
| `CAMERA` / `RECORD_VIDEO` / `FLASHLIGHT` | 危险 | 可能「拍天空/实景」 | 动态验证是否仅在功能页触发 |
| `READ_MEDIA_IMAGES` / `VIDEO` | 危险 | 媒体相关 | |
| `WRITE/READ_EXTERNAL_STORAGE` | 危险 | 缓存/图片 | |
| `PACKAGE_USAGE_STATS` (maxSdk 28) | 特殊 | 存疑 | 可能用于桌面角标；需政策说明 |
| `REQUEST_INSTALL_PACKAGES` | 特殊 | 存疑 | 应用内更新？需说明 |
| `QUERY_ALL_PACKAGES` | — | **未声明** | 静态未见 |
| `READ_PHONE_STATE` / `READ_CONTACTS` / `READ_SMS` | 危险 | **未直接声明** | 但代码里仍有标识符相关 API（见 2.2） |
| `GET_TASKS` | 普通(旧) | 弱 | |
| 厂商 OAID 相关（asus/vivo/oppo/nemu/freemme…） | 自定义 | 广告标识 | 指向 OAID 采集 |
| 穿山甲 `TT_PANGOLIN` | 自定义 | 广告 | 字节广告 SDK |
| 个推 `GetuiService` | 自定义 | 推送 | |
| 各厂商 Push/Badge 权限簇 | 自定义 | 推送/角标 | 数量很多 |

**S-01 小结：** 定位权限与产品匹配度高；背景定位、活动识别、安装包、使用情况统计属于「需政策写清」的扩展面。未见通讯录/短信危险权限声明。

### 2.2 敏感 API / 字符串线索（Jadx 全树命中文件数）

| 检查项 | 约命中文件数 | 说明 |
|--------|--------------|------|
| `getDeviceId` | 44 | 多在 SDK/兼容层，需动态看是否仍调用 |
| `getImei` / `getMeid` | 18 / 4 | 同上 |
| `getSubscriberId` / `getSimSerialNumber` | 5 / 3 | 同上 |
| `ANDROID_ID` | 9 | 常见回退标识 |
| `getMacAddress` | 29 | Android 10+ 多为占位值，仍可能被 SDK 调用 |
| `getLastKnownLocation` / `requestLocationUpdates` | 7 / 4 | 业务 `moji`/`com.moji` 目录下未直接命中（多在第三方） |
| `ClipboardManager` / `getPrimaryClip` | 8 / 1 | 需动态确认 |
| `ContactsContract` | 3 | 低优先 |
| `http://` | 86 | 多为文档/常量；流量线再验 |
| `addJavascriptInterface` | 16 | WebView 桥，攻击面/数据面 |
| OAID 相关 | **323** | 广告标识体系庞大（com.zui.deviceids、bun 等） |

### 2.3 第三方 SDK 初判（存在包名/引用信号）

| SDK / 体系 | 用途假设 |
|------------|----------|
| 友盟 `com.umeng*` | 统计/认证 |
| 个推 `com.igexin` / `com.getui` | 推送 |
| 穿山甲 / 字节 `bytedance` / `com.ss.android` / `TT_PANGOLIN` | 广告 |
| 百度 `com.baidu` | 地图/定位/账号等（需细分） |
| 高德 `amap` / `autonavi` | 地图定位 |
| 腾讯 `com.qq.e` | 广告 |
| 阿里系 `alibaba` / `taobao` / `aliyun` | 多种组件 |
| 小米/华为/OPPO/vivo/三星等 | 推送、OAID、角标 |
| `com.zui.deviceids` / `com.bun` | 移动安全联盟 OAID |
| Flutter | 混合开发 |

### 2.4 静态假设（待动态验证）

| 假设 ID | 描述 | 优先级 | 验证计划 |
|---------|------|--------|----------|
| H-01 | 冷启动即读取设备标识（IMEI/Android ID/OAID 其一） | 高 | Frida `device_id.js` 冷启动 |
| H-02 | 首次进入主页请求精确定位 | 高 | `location.js` + 操作剧本 |
| H-03 | 存在后台定位（`ACCESS_BACKGROUND_LOCATION`） | 中 | 退后台后观察 |
| H-04 | 广告 SDK 在启动阶段初始化并可能采集标识 | 高 | 启动 30s 内 Hook 日志 |
| H-05 | WebView 桥暴露到非受信页面 | 低 | 静态细读 + 流量 |
| H-06 | 政策是否披露背景定位/OAID/穿山甲 | 高 | 对照政策 C-xx |

**静态证据目录：** `evidence/com.moji.mjweather/static/`（待补 E-A1-sta-01… 权限表截图/摘录）

---

## A2 豆瓣（`com.douban.frodo` 7.133.0）

### 2.1 权限（Manifest，危险/敏感摘录）

| 权限 | 类型 | 与功能相关？ | 观察 |
|------|------|--------------|------|
| `ACCESS_FINE_LOCATION` / `COARSE` | 危险 | 中（同城/附近？） | 内容社区非核心，政策应说明 |
| `CAMERA` | 危险 | 是（发动态/扫码） | 合理 |
| `RECORD_AUDIO` | 危险 | 可能（语音） | 动态看触发点 |
| `READ_MEDIA_IMAGES` / `VIDEO` | 危险 | 是 | |
| `QUERY_ALL_PACKAGES` | 特殊 | **已声明** | 应用列表相关，合规敏感 |
| `REQUEST_INSTALL_PACKAGES` | 特殊 | 存疑 | |
| `NFC` | 普通 | 弱 | |
| `USE_CREDENTIALS` | 普通(旧) | 账号 | |
| 穿山甲 `TT_PANGOLIN` | 自定义 | 广告 | |
| 小米/OPPO/荣耀等 Push | 自定义 | 推送 | |
| `READ_CONTACTS` / `READ_SMS` / `READ_PHONE_STATE` | 危险 | **未直接声明** | 代码层仍有标识符 API |
| OAID 厂商权限簇 | 自定义 | 广告标识 | 与 A1 类似 |

**S-01 小结：** 有定位、相机、录音、`QUERY_ALL_PACKAGES`——后两者对内容社区值得在政策对照里重点写。

### 2.2 敏感 API / 字符串线索

| 检查项 | 约命中文件数 | 说明 |
|--------|--------------|------|
| `getDeviceId` | 53 | 业务包 `com.douban.push` 等有 **自研 deviceId** 字段（未必是 IMEI） |
| `getImei` / `getMeid` | 23 / 2 | |
| `getSubscriberId` | 7 | |
| `ANDROID_ID` | 2 | 全树较少 |
| `getMacAddress` | 24 | |
| 定位 API | 7 / 9 | |
| `ClipboardManager` | 30 | **比 A1 更密**；业务侧多见写剪贴板（分享），读取需动态确认 |
| `getPrimaryClip` | 6 | |
| `http://` | 93 | |
| `addJavascriptInterface` | 20 | |
| OAID | 143 | |

**业务侧亮点（静态）：**  
`com.douban.push.internal.Settings.getDeviceId()`、`ChatConfig` 含 deviceId 字段——说明豆瓣有**应用内设备标识抽象**，动态要区分「自研 ID」vs「系统 IMEI」。

### 2.3 第三方 SDK 初判

| SDK / 体系 | 用途假设 |
|------------|----------|
| 友盟 | 统计 |
| 穿山甲/字节 | 广告 |
| 阿里 `mtopsdk` / `alibaba` / `alipay` | 网络/支付组件 |
| 高德 `amap` | 地图 |
| 京东 `jd` / `kepler` | 电商/广告 |
| 腾讯 `com.qq.e` | 广告 |
| 小米/华为/OPPO 等 | 推送 |
| `com.mob` | 可能分享/认证组件 |
| Flutter | 混合开发 |
| 自研 `com.douban.push` / artery | 推送 |

### 2.4 静态假设

| 假设 ID | 描述 | 优先级 | 验证计划 |
|---------|------|--------|----------|
| H-10 | 启动读取系统设备标识（IMEI/MAC/AndroidId）供统计/广告 | 高 | Frida 冷启动 |
| H-11 | `QUERY_ALL_PACKAGES` 对应读取已安装应用列表 | 高 | `packages.js` |
| H-12 | 定位仅在附近/同城功能触发（非冷启动） | 中 | 操作剧本对比 |
| H-13 | 剪贴板主要为写入（口令/链接），读取需证实 | 中 | `clipboard.js` |
| H-14 | 政策是否披露广告 SDK 与应用列表 | 高 | 合规表 |
| H-15 | 自研 deviceId 如何生成、是否上传 | 高 | 动态 + 流量 |

**静态证据目录：** `evidence/com.douban.frodo/static/`

---

## 横向对比（静态阶段）

| 维度 | A1 墨迹 | A2 豆瓣 |
|------|---------|---------|
| 定位必要性 | 高（产品核心） | 中（功能增强） |
| 后台定位权限 | **有** | 无 |
| `QUERY_ALL_PACKAGES` | 无 | **有** |
| 广告 SDK 信号 | 穿山甲等，OAID 面极大 | 穿山甲 + 京东等 |
| 标识符 API 命中 | 多 | 多，且有自研 deviceId |
| 剪贴板 | 较少 | 较多 |
| 静态可分析性 | 可用（有 ijiami 痕迹） | 好 |

---

## 下一步（动态）

按优先级：

1. A1 冷启动：`device_id.js` + `location.js`  
2. A2 冷启动：`device_id.js` + `packages.js`  
3. 再按假设补通讯录/剪贴板  

证据写入 `evidence/<pkg>/dynamic/`，编号 E-xx-dyn-nn。
