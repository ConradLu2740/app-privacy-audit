"""APP 隐私合规检测流水线。

模块划分见 docs/design/llm-compliance-engine.md 第 7 节。

当前实现范围：LLM 合规研判引擎骨架（schema / llm / policy / regulation / align / report）。
静态分析、动态 Hook、流量采集仍由 scripts/ 下的手工流程产出，
经整理后转为 BehaviorFact 输入本引擎。
"""

__version__ = "0.1.0"
