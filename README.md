# 💧 大语言模型水印鲁棒性与安全性分析 (LLM Watermarking Analysis)

本仓库包含了对大语言模型水印方案（基于 Logit 偏置的统计水印）的复现、对抗攻击测试以及基于密码学视角的安全性深度分析。本项目作为《现代密码学》课程大作业完成。

## 🚀 项目概览

本项目旨在通过实证研究验证 LLM 水印在以下维度的表现：
1. **有效性 (Effectiveness)**: 在不同熵值的文本中植入可检测信号的能力。
2. **鲁棒性 (Robustness)**: 在遭受语义重写攻击（T5 Paraphrase）时的信号留存率。
3. **不可区分性 (Indistinguishability)**: 从统计频率角度分析水印植入是否会导致非忽略的分布偏移。

## 🛠️ 核心组件

- `orchestrator.py`: 实验流水线编排器，负责自动化的生成、攻击与评估全流程。
- `core_classes.py`: 封装了生成器 (Generator)、攻击器 (Attacker) 和评估器 (Evaluator) 的核心逻辑。
- `deep_analysis.py`: 密码学深度分析工具，计算 KL 散度与 TVD 指标，识别侧信道泄漏点。
- `visualize_results.py`: 可视化工具，生成用于报告的出版级图表。
- `watermark_processor.py`: 水印逻辑核心实现（继承自 LogitProcessor）。

## 📊 快速复现流程

### 1. 环境准备
确保已安装所需的依赖库（建议使用 Conda 环境）：
```bash
pip install torch transformers scipy pandas matplotlib seaborn jinja2
```

### 2. 模型下载
本项目依赖以下预训练模型（请确保路径正确或使用环境变量配置）：
- 生成模型: `facebook/opt-1.3b`
- 攻击模型: `Vamsi/T5_Paraphrase_Paws`
- 评判模型: `gpt2-large`

### 3. 执行实验管线
运行编排脚本，该脚本将自动完成生成、攻击和基础指标计算：
```bash
python orchestrator.py
```
完成后将生成 `experiment_results.jsonl` 文件。

### 4. 密码学深度分析
运行深度分析脚本以量化统计安全性：
```bash
python deep_analysis.py
```
分析结果将保存至 `cryptographic_metrics.json`。

### 5. 生成可视化报表
运行绘图脚本生成实验图表：
```bash
python visualize_results.py
```
所有图表将保存至 `report/` 文件夹。

## 📈 实验结论摘要

| 指标 | 实验值 | 结论 |
| :--- | :--- | :--- |
| **平均 Z-score (原始)** | 9.92 | 水印信号极强，检测置信度高 |
| **Z-score 留存率 (攻击后)** | 52.65% | 表现出较强的语义攻击抵抗力 |
| **KL 散度 (P_w \|\| P_n)** | 0.2508 | 存在非忽略的分布偏置，具有侧信道泄漏风险 |
| **主要泄漏特征** | `\n`, ` in`, ` on` | 高频 Token 的概率分布受水印算法影响显著 |

## 📄 引用
本项目参考了以下论文：
- [A Watermark for Large Language Models (Kirchenbauer et al., ICML 2023)](https://arxiv.org/abs/2301.10226)
- [On the Reliability of Watermarks for Large Language Models (Kirchenbauer et al., ICLR 2024)](https://arxiv.org/abs/2306.04634)
