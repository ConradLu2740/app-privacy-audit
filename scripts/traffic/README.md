# 流量分析辅助说明

## 推荐路径

1. **mitmproxy / Charles**：解密 HTTPS 后看字段（需处理用户证书信任 / unpinning）  
2. **PCAPdroid**：设备侧抓包，明文 HTTP 与 SNI 很有用  
3. 失败时：只写「HTTPS 未解密」局限，用时间相关 + 静态域名列表交叉推测（谨慎表述）

## mitmproxy 冒烟

```bash
mitmproxy --listen-host 0.0.0.0 --listen-port 8080
# 模拟器 Wi-Fi 代理指向主机 IP:8080，并安装 mitmproxy CA
```

常用过滤（界面内）：

```text
~u /api
~d example.com
~c 200 & q
```

导出关注请求后，按 [evidence 规范](../../evidence/README.md) 脱敏入库。

## 对齐动态时间线

1. 先跑 Frida 记 `T+`  
2. 再复现同一操作路径抓包  
3. 报告中并列时间戳，增强「调用 → 上传」说服力  

## 安全与合规

- 只抓自有测试账号与模拟器流量  
- 入库前脱敏 token / 手机号 / 精确位置  
- 不提交原始 PCAP  
