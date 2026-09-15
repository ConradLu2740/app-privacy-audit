# E-A2-trf-01 — 豆瓣流量观测（PCAPdroid）

> 日期：2026-09-15  
> 设备：小米 14 Ultra（arm64-v8a，无 root）  
> 工具：PCAPdroid 1.8.6（设备侧 VPN 抓包）  
> 样本：豆瓣 7.133.0 / `com.douban.frodo`  
> 结论：**仅访问豆瓣自有域名，未见第三方 SDK 域名**

---

## 1. 方法说明

- 同 `E-A3-trf-01`：PCAPdroid 连接级捕获，HTTPS 载荷加密不可见
- 观测：冷启动 + 首页推荐流加载约 60 秒

## 2. 观测到的域名

| 域名 | 用途推断 | 协议 | 样本流量 |
|------|----------|------|----------|
| `frodo.douban.com` | 主 API（包名前缀） | TLS/HTTPS | 61.8 KB+ |
| `amonsul.douban.com` | 自研埋点/分析 | HTTPS | 8.1 KB, 5.0 KB |
| `erebor.douban.com` | 内部服务 | TLS | 7.6 KB |
| `www.douban.com` | Web 内容 | TLS | 17.7 KB |
| `accounts.douban.com` | 账号服务 | DNS | — |
| `img1/3/9.doubanio.com` | 图片 CDN | HTTPS | 6.4–79.3 KB |

## 3. 关键发现

1. **全部为豆瓣自有域名**（`*.douban.com` / `*.doubanio.com`）
2. **未观测到第三方 SDK 域名**（如友盟 `umeng`、京东 `jd`、阿里 `aliyun` 等）
   - 静态分析中发现的友盟/京东/阿里 SDK 在本次 60s 前台会话中**未触发网络请求**
   - 可能原因：冷启动未登录、SDK 懒加载、或仅在特定场景上报
3. `amonsul.douban.com` 为豆瓣自研埋点域名，与静态发现的 `com.douban.push` deviceId 对应

## 4. 局限性

- 连接级观测，无法确认请求路径/参数/body
- 未登录状态，登录后可能触发更多 SDK
- 60s 窗口可能遗漏低频上报

## 5. 证据文件

| 文件 | 说明 |
|------|------|
| `E-A2-trf-01-connections.png` | 主要连接列表 |
| `E-A2-trf-01-more.png` | 更多域名（CDN/账号） |
