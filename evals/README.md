# LLM 合规研判引擎评测集（eval set）

给 `audit/` 引擎一套带标准答案的评测用例，量化研判质量，兼作回归测试。

## 运行

```bash
# 离线模式（默认）：FakeProvider 回放固定响应，无需网络与 API key，结果确定可复现
python evals/run_eval.py

# 实测模式：用真实 LLM 跑抽取与语义判定，验证引擎对真实模型的稳健性
# （需 config.yaml 或 AUDIT_LLM_* 环境变量）
python evals/run_eval.py --live
```

报告写入 `out/eval_report.md`；退出码非 0 表示存在失败用例，可直接挂 CI。

## 用例清单（evals/cases/）

| 用例 | 覆盖能力 | 判定路径 | 期望 |
|------|----------|----------|------|
| ev1-before-consent | 同意前收集（时序） | 规则引擎 | COLLECT_BEFORE_CONSENT / device_id |
| ev2-beyond-scope | 超范围收集（差集 + 必要性语义判定） | 语义 | BEYOND_SCOPE / installed_apps |
| ev3-undeclared-sharing | 未声明第三方共享（集合差 + 共享语义判定） | 语义 | UNDECLARED_SHARING / location |
| ev4-insecure-transport | 明文传输敏感数据 | 规则引擎 | INSECURE_TRANSPORT / device_id |
| ev5-hallucination-gate | **防幻觉闸门**：编造引证必须被丢弃 | 闸门 1a | 零判定 + dropped_bad_quote=1 |
| ev6-consistent-clean | 干净对照（不误报） | 全链路 | 零判定 |

## 评分口径

- 判定维度：`(violation_type, data_type)` 对上的 precision / recall / F1
- 闸门断言：抽取统计（原始声明数、因编造引证丢弃数、接受数）与期望值逐一核对
- ev5 是本评测集的价值核心：证明引擎在「LLM 返回幻觉内容」时不会产出无证据判定

## 新增用例

复制任意 case 目录，改四个文件：

```text
policy.txt           隐私政策文本（条款间空行分段，与 split_clauses 口径一致）
facts.json           行为事实（BF-*，格式同 fixtures/facts_a3.json）
fake_responses.json  FakeProvider 按键匹配响应（key 取提示词中的特征串，多 key 命中时最长 key 优先）
expected.json        标准答案：expect_findings + 可选 gates 断言
```

注意：fake 响应的 `quote` 必须是 policy.txt 原文子串，否则会被闸门 1a 丢弃（ev5 就是利用这一点构造的）。
