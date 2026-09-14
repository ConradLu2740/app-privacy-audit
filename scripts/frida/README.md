# Frida Hook 脚本

最小可复现脚本集，按敏感点拆分。先跑单点，再上 `all_hooks.js`。

## 前置

- `frida` 客户端与设备端 `frida-server` **版本一致**
- 已 `adb devices` 能看到目标
- 包名自行替换

## 用法

```bash
# 冷启动并注入
frida -U -f com.example.app -l scripts/frida/device_id.js --no-pause

# App 已启动时附加
frida -U -n "示例应用" -l scripts/frida/location.js

# 全量（噪声大，适合第一轮摸底）
frida -U -f com.example.app -l scripts/frida/all_hooks.js --no-pause
```

## 脚本列表

| 文件 | 覆盖检查项 |
|------|------------|
| `device_id.js` | D-01 D-02 D-03 |
| `location.js` | D-05 D-06 |
| `contacts.js` | D-07 |
| `clipboard.js` | D-09 |
| `packages.js` | D-10 |
| `sensors_audio.js` | D-11（相机/录音粗钩子） |
| `all_hooks.js` | 上述并集 |

## 读输出

统一前缀：

```text
[HOOK][category] method args -> result
```

把关键行按 [evidence 规范](../../evidence/README.md) 脱敏归档。

## 注意

- 某些 ROM/加固环境 spawn 失败，改用 `-n` 附加  
- 返回值可能是 `null`（权限拒绝），**调用本身**仍是证据  
- 脚本只做观测，不做利用、不上传数据  
