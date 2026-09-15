# E-A3-trf-01 — NewPipe 流量观测（PCAPdroid）

> 日期：2026-09-15  
> 设备：小米 14 Ultra（arm64-v8a，无 root）  
> 工具：PCAPdroid 1.8.6（设备侧 VPN 抓包）  
> 样本：NewPipe 0.29.1 / `org.schabi.newpipe`  
> 结论：**仅访问 `www.youtube.com`，未见第三方追踪/分析域名**

---

## 1. 方法说明

- 无 root，mitmproxy 用户 CA 不被 NewPipe 信任（Android 7+ 默认行为），无法解密 HTTPS 载荷
- 改用 **PCAPdroid**（Android VPN API）在设备侧捕获连接级元数据
- 观测维度：目标域名 / 协议 / 端口 / 流量大小（**不含 HTTP 载荷**）

## 2. 观测结果

NewPipe 启动并触发搜索后，捕获到以下连接：

| # | 协议 | 端口 | 目标 | 大小 | 状态 |
|---|------|------|------|------|------|
| 1 | DNS | 53 | `www.youtube.com` | 138 B | 已关闭 |
| 2 | TLS | 443 | `www.youtube.com` | 825 B | 已关闭 |
| 3 | TCP | 443 | `www.youtube.com` | 280 B | 错误（VPN 拦截） |
| 4 | TCP | 443 | `www.youtube.com` | 280 B | 错误（VPN 拦截） |

**关键发现：**

1. **唯一目标域名** = `www.youtube.com`（YouTube 官方）
2. **未观测到** 任何第三方分析 / 广告 / 崩溃上报域名（如 Sentry、Firebase、Umeng 等）
3. 与静态分析结论一致：NewPipe 无 OAID / 设备标识 SDK，网络面极窄

## 3. 局限性

- HTTPS 载荷加密，**无法确认请求路径与参数**
- VPN 拦截导致部分连接显示「错误」，不影响域名级结论
- 未覆盖 IPv6 / QUIC 流量（PCAPdroid 默认过滤）

## 4. 证据文件

| 文件 | 说明 |
|------|------|
| `E-A3-trf-01-connections.png` | NewPipe 连接列表（搜索过滤后） |
| `E-A3-trf-01-allapps.png` | 全应用连接列表（对照） |

## 5. 与政策对照

NewPipe GDPR 隐私政策声明「不收集个人数据、不使用第三方追踪」。  
本观测**未发现矛盾**：网络面仅 YouTube 官方域名，符合政策描述。

> 注意：连接级观测 ≠ 载荷级证明；崩溃上报等低频路径可能未触发。
