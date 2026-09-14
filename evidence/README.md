# Evidence 规范

证据是报告结论的唯一支撑。本目录**只放脱敏后的可公开材料**。

## 目录布局

```text
evidence/
├── README.md                 # 本说明
├── _template/                # 新样本先复制
│   ├── static/
│   ├── dynamic/
│   └── traffic/
└── <package.name>/           # 例如 com.example.app
    ├── static/
    ├── dynamic/
    └── traffic/
```

复制模板：

```bash
# 在仓库根目录
cp -r evidence/_template evidence/<package.name>
```

## 编号规则

| 前缀 | 含义 | 示例 |
|------|------|------|
| `E-<app>-sta-nn` | 静态证据 | `E-A1-sta-01` |
| `E-<app>-dyn-nn` | 动态证据 | `E-A1-dyn-03` |
| `E-<app>-trf-nn` | 流量证据 | `E-A1-trf-02` |

`<app>` 建议用样本表 ID（A1/A2/A3），短且稳定。

## 单条证据最小字段

在对应目录放 `E-xx-*.md`（或截图 + 同名 md 说明）：

```markdown
# E-A1-dyn-01

- **结论一句话：** 冷启动 T+1.2s 调用 TelephonyManager.getImei
- **样本：** A1 / com.example.app / 1.2.3 (45)
- **步骤：**
  1. frida -U -f com.example.app -l scripts/frida/device_id.js --no-pause
  2. 杀进程后冷启动，观察首屏
- **关键输出（脱敏）：**
  ```
  [T+1.2s] getImei slot=0 stack=com.example...
  ```
- **关联假设/检查项：** H-01 / D-01
- **附件：** `E-A1-dyn-01.log`（已脱敏） / 截图 `E-A1-dyn-01.png`
- **采集时间：** 2026-09-20 14:02 +08:00
```

## 脱敏清单（入库前必过）

- [ ] 去掉真实手机号、邮箱、身份证、精确住址  
- [ ] Token / Cookie / Authorization 打码或截断  
- [ ] 广告 ID / 完整设备号可保留格式但打码中段  
- [ ] 账号昵称可保留，密码永不可出现  
- [ ] 截图中的通知栏、输入法候选词检查一遍  
- [ ] PCAP：不提交原始文件；只提交过滤说明 + 字段摘录表  

## 流量证据建议格式

```markdown
# E-A1-trf-01

- **结论：** 向 api.example.com 发送明文 JSON，含 androidId 字段
- **过滤：** host contains "api.example.com" and http
- **时间对齐：** 与 E-A1-dyn-01 同一冷启动窗口
- **摘录（脱敏）：**
  | 字段 | 值（脱敏） |
  |------|------------|
  | androidId | a1b2****ef9 |
  | ts | 1726... |
- **局限：** HTTPS 其他主机未解密
```

## 不要提交

- 完整 `.apk` / `.aab`  
- 原始 `.pcap` / `.pcapng`  
- 未脱敏的 `frida` 全量日志  
- 含个人账号的隐私政策导出 PDF（可存本地，报告只摘录句子）  

## 与报告的关系

报告正文只写编号与一句话结论，细节留在本目录。读者应能：

`报告结论 → 证据编号 → evidence 路径 → 按步骤复现`  
