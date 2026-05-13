# 红绿名单水印方案的独立复现与统计安全性检验

基于 Kirchenbauer 等人 (ICML 2023) 的红绿名单 Logit 偏置水印方案的独立复现研究。在 OPT-1.3B 模型上完整运行生成 → 攻击 → 检测管道，补充了自相关检验、TVD/KL 分布距离、高偏置 token 识别和定向替换实验四项统计检验。

> **论文**: [watermark_report.pdf](report/watermark_report.pdf)  
> **课程**: 深圳大学 · 现代密码学 · 2025-2026 学年  
> **仓库**: https://github.com/AatroxChen77/2026-llm-watermark-security

---

## 核心发现

| 指标 | 值 | 说明 |
|------|-----|------|
| Z-score (原始) | 10.04 [Bootstrap 95% CI: 9.18, 10.92] | 远高于检测阈值 τ=4.0 |
| Z-score (T5 攻击后) | 5.24 [Bootstrap 95% CI: 4.17, 6.34] | 仍高于阈值，检测率 90% |
| Z-score 留存率 | 52.7% | 均一翻转模型拟合 ρ ≈ 0.239 |
| PPL 增幅 | 13.40 → 16.06 (+19.9%) | 轻微质量损失 |
| TVD(P_w, P_n) | 0.281 [Bootstrap 95% CI: 0.304, 0.403] | 偏移集中在少数高频功能词 |
| D_KL(P_w \| P_n) | 0.251 | 信息论角度的补充度量 |

---

## 复现步骤

### 1. 环境
```bash
conda env create -f environment.yml  # 或 pip install torch transformers scipy pandas matplotlib seaborn
```

### 2. 模型
生成模型 `facebook/opt-1.3b`、攻击模型 `Vamsi/T5_Paraphrase_Paws`、评估模型 `gpt2-large` 由 HuggingFace 自动下载。

### 3. 按序执行

| 步骤 | 脚本 | 说明 | CUDA |
|------|------|------|------|
| 1 | `python reproduce_r3.py` | 生成原始文本与水印文本 | 需 |
| 2 | `python compute_t5_metrics.py` | T5 释义攻击 | 需 |
| 3 | `python compute_rational_ppl.py` | PPL 评估 | 需 |
| 4 | `python reproduce_r4.py` | 深度分析（自相关、TVD、Bootstrap） | 否 |
| 5 | `python reproduce_r6.py` | 定向替换实验 | 需 |
| 6 | `python compute_rational_sensitivity.py` | 敏感性扫描（定向 vs 随机） | 需 |
| 7 | `python visualize_results.py` | 生成论文图表 | 否 |
| 8 | `python plot_rational_sensitivity.py` | 敏感性曲线 | 否 |

步骤 7-8 可在本地 `conda run -n plotting` 环境下秒出，无需 CUDA。

---

## 项目结构

```
├── reproduce_r3.py              # 生成实验
├── reproduce_r4.py              # 统计检验（CPU）
├── reproduce_r6.py              # 定向替换实验
├── compute_t5_metrics.py        # T5 攻击
├── compute_rational_ppl.py      # PPL 计算
├── compute_rational_sensitivity.py  # 敏感性扫描（服务器）
├── plot_rational_sensitivity.py # 敏感性画图（本地）
├── visualize_results.py         # 论文图表生成（本地）
├── core_classes.py              # 水印生成器/攻击器/评估器
├── watermark_processor.py       # Logit 偏置核心
├── experiment_results.jsonl     # 10 组样本的实验数据
├── rational_sensitivity_results.json  # 敏感性曲线数据
├── report/
│   ├── watermark_report.tex     # 论文 LaTeX 源码
│   ├── watermark_report.pdf     # 论文 PDF
│   ├── references.bib           # 参考文献
│   └── *.pdf / *.png            # 5 张出版级图表
└── log/                         # 复现运行日志
```

**注意**：项目目录中原包含若干 fork 上游的参考脚本（如 `orchestrator.py`、`app.py`、`demo_watermark.py` 等），为保持仓库清爽已在最新提交中清除。完整历史可在 Git 记录中回溯。

---

## 适用范围与局限

- 全部实验基于 OPT-1.3B 单一模型 + T5 Paraphrase-PAWS 单一攻击器，观测不应在未经检验的情况下外推到其他模型族
- TVD 衡量的是边际分布的 token 级偏置，不等同于序列级 IND 安全性论证
- 定向替换实验仅覆盖 0%–20% 替换率，且攻击策略为朴素词频替换，不涉及语义保持的高级攻击
- 样本规模 n=10，所有百分比指标请参考论文中的 Bootstrap CI

## 引用

本项目的理论基础来源于：

- Kirchenbauer et al. *A Watermark for Large Language Models*. ICML 2023.
- Kirchenbauer et al. *On the Reliability of Watermarks for Large Language Models*. ICLR 2024.
- Christ, Gunn & Zamir. *Undetectable Watermarks for Language Models*. 2023.
- Jovanović, Staab & Vechev. *Watermark Stealing in Large Language Models*. ICML 2024.
