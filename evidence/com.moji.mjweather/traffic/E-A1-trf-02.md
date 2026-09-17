# E-A1-trf-02 — 墨迹天气流量观测（PCAPdroid，首启后主界面）

> 日期：2026-09-17  
> 设备：小米 14 Ultra（arm64-v8a，无 root）  
> 工具：PCAPdroid 1.8.6（设备侧 VPN 抓包，全应用捕获后按应用名过滤）  
> 样本：墨迹天气 9.0942.02 / `com.moji.mjweather`  
> 场景：首启完成隐私协议 + 定位授权（仅使用期间允许），进入主界面后下拉刷新、浏览预报与资讯流约 60s  
> 结论：**首启即触发大量第三方 SDK 上报；观测到 535 条连接、74 个独立主机，其中约 45% 连接为第三方域名**

---

## 1. 方法说明

- 承接 `E-A1-trf-01`（受阻取证：首启前卡在 splash 无法采集）；本次为人工完成首启授权后的复测
- PCAPdroid 全应用捕获（目标应用选择器在本机 HyperOS 上列表为空，改用全量捕获 + 连接页按应用名「墨迹天气」过滤）
- 连接级元数据（域名/IP/端口/协议/字节数/时间戳），无载荷；原始 CSV 含设备内网 IP，不入库
- 墨迹相关连接观测窗口：21:24:20 – 21:25:17（约 57s）
- 导出方式：PCAPdroid 连接页 → 更多选项 → 保存到文件（CSV），本地汇总后按证据规范脱敏

## 2. 总量

| 指标 | 数值 |
|------|------|
| 墨迹天气连接数 | 535（占全部捕获连接的 ~68%） |
| 独立主机数 | 74 |
| 发送 / 接收 | 1.79 MB / 19.34 MB |
| 协议分布 | HTTPS 367 / DNS 110 / 明文 HTTP 50 / TCP 4 / TLS 4 |

## 3. 第三方域名观测（按厂商分组）

与 `E-A1-sta-01` 静态发现的 SDK 指纹（友盟/个推/穿山甲/高德/百度等）**互证**：

| 厂商 / SDK | 代表域名 | 连接数 | 流量 | 静态指纹来源 |
|-----------|----------|-------:|-----:|--------------|
| 京东联盟/京东广告 | `xlog.jd.com`、`dsp-x.jd.com`、`janapi.jd.com` | 69 | 419 KB | sta-01 京东 SDK |
| 腾讯广告 GDT（优量汇） | `win.gdt.qq.com`、`mi.gdt.qq.com`、`sdk.e.qq.com`、`*.ugdtimg.com` | 49 | 887 KB | sta-01 广点通 |
| 高德定位 | `dualstack-mpsapi.amap.com`、`dualstack-arestapi.amap.com` | 40 | 4.59 MB | sta-01 高德 SDK |
| 穿山甲/字节（Pangle） | `api-access.pangolin-sdk-toutiao*.com`、`log-api.pangolin-sdk-toutiao-b.com`、`log.zijieapi.com`、`apmplus.volces.com`、`*.pglstatp-toutiao.com` | 27 | 1.54 MB | sta-01 穿山甲 |
| 微信小程序云 | `prewxacode.wxqcloud.qq.com.cn` | 4 | 1.00 MB | — |
| 阿里 tanx | `opehs.tanx.com`、`et.tanx.com` | 5 | 98 KB | sta-01 阿里 mtop 生态 |
| 百度广告 | `mobads.baidu.com`、`hmma.baidu.com`、`bjimp.voiceads.cn` | 9 | 32 KB | sta-01 百度 SDK |
| 个推 | `ido.gepush.com` | 8 | 29 KB | sta-01 个推 |
| 友盟 | `cnlogs.umeng.com` | 3 | 15 KB | sta-01 友盟 |
| 秒针监测 | `g.cn.miaozhen.com` | 4 | 17 KB | — |
| 墨迹自有 | `*.moji.com`、`*.mojicdn.com`、`moji002.com` 等 | 295 | 11.3 MB | — |
| 其他/未分类 | `b.qchannel03.cn`、`bytesfield.com`、`tfogc.com` 等 | 22 | 340 KB | — |

## 4. 关键发现

1. **首启 60s 内第三方 SDK 全面激活**：京东、腾讯 GDT、穿山甲、高德、百度、个推、友盟均有实际网络连接，与静态 SDK 指纹一一对应——静态命中在本次得到流量侧实证
2. **明文 HTTP 50 条**：主要为墨迹自有日志/资源端点（`v1.log.moji.com` 13、`cdn.moji.com` 10、`v2.log.moji.com` 5、`stat.moji.com` 1、`oss4bpc.moji.com` 7、`ad.api.moji.com` 4 等）及第三方 `bjimp.voiceads.cn`、`p26-be-pack-sign.pglstatp-toutiao.com`；日志类端点走明文存在被嗅探/篡改风险（对齐检查项 T-* / 06 章风险表）
3. **广告 SDK 占比高**：京东+GDT+穿山甲+百度+tanx 合计 159 条连接、约 2.4 MB，与「天气工具类 App 广告变现」画像一致
4. 高德定位流量最大单第三方（4.59 MB），与授予「使用期间允许定位」后的预期行为一致
5. 对比 `E-A2-trf-01`（豆瓣仅自有域名）：同窗口口径下墨迹的第三方暴露面显著更大

## 5. 局限性

- 连接级观测，无法确认请求路径/参数/body（HTTPS 载荷加密）
- 未登录状态；登录后可能触发更多账号/推荐链路
- 57s 前台窗口，低频上报（如启动次数统计之外的后台上报）可能遗漏
- 全应用捕获，墨迹连接按应用名过滤，UID 归属以 PCAPdroid 判定为准

## 6. 证据文件

| 文件 | 说明 |
|------|------|
| `E-A1-trf-02-connections.png` | PCAPdroid 连接页按「墨迹天气」过滤后的列表截图 |
| 本文件 §2–§3 | 由 PCAPdroid 导出 CSV 汇总（原始 CSV 不入库，含内网 IP） |
