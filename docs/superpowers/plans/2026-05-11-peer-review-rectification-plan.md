# 评审整改计划 (Peer Review Rectification Plan) - v2.0 (整合硬核理论反馈)

**日期:** 2026-05-11
**关联评审:** 综合第一份同行评审与第二份“硬核理论”审稿意见
**核心目标:** 在保持实验数据完整性的基础上，对论文进行一次“学术语言精准化手术”，消除术语过界（Overreach），并补充统计学假设深度。

---

## 1. 术语精准化调整 (学术语言手术 - 最高优先级)
针对审稿人指出的“术语过载”问题，在全文范围进行降级与精准化：
*   **不可区分性**: 将所有关于“不满足 IND-CPA”的类比，替换为“不满足严格统计不可区分性（Statistical Indistinguishability）”或“存在统计显著的可检测性（Distributional Detectability）”。
*   **泄漏定义**: 将“侧信道泄漏（Side-channel Leakage）”统一改为“统计泄漏（Statistical Leakage）”或“分布偏差（Distributional Bias）”。
*   **原语定义**: 在 3.1 节，将 PRF 的绝对定义弱化为“基于密钥的伪随机词表划分（Keyed Pseudorandom Partitioning）”。

## 2. 统计学理论深度补充 (第 3.2 节 & 第 5 节)
*   **IID 悖论讨论**: 在 3.2 节 Z 检验部分，补充讨论 LLM token 的自回归（Autoregressive）特性与 IID（独立同分布）假设之间的矛盾。指出 Z 检验在此场景下依赖于大数定律（LLN）和中心极限定理（CLT）的**渐进近似（Asymptotic Approximation）**。
*   **安全参数定义**: 明确 $\lambda$ 与密钥长度或上下文窗口 $h$ 的逻辑关联。

## 3. 形式化建模与推导 (第 5.2 节 & 第 5.4 节)
*   **DSC 信道推导**: 在 5.2 节正式引入离散对称信道公式。假设翻转概率为 $p$，推导 $Z_{attacked} \approx (1 - 2p) Z_{original}$。
*   **博弈论建模**: 在 5.4 节将“理性博弈者攻击”形式化为一个受约束的优化问题：
    *   $\min Z(s')$ subject to $Sim(s, s') > \tau$ (其中 $Sim$ 为语义相似度，$\tau$ 为保真度阈值)。

## 4. 实验验证与 PoC (第 5.4 节)
*   **目标文件:** `lm-watermarking/rational_attack_poc.py` (新增)
*   **行动:** 编写 Python 脚本，针对 `\n`、`in`、`on` 等识别出的“高统计泄漏 Token”执行定向替换策略。
*   **数据更新:** 将“定向替换攻击”与“盲目重写攻击（T5）”的衰减效率进行对比，存入 5.4 节，证明攻击者的“理性”收益。

## 5. 参考文献与规范化
*   **目标文件:** `lm-watermarking/report/references.bib`
*   **行动:** 
    *   更新 Kirchenbauer et al. (2024) 至 ICLR 正式录用版本。
    *   检查全文 LaTeX 数学符号的一致性。

## 6. 最终编译与校对
*   运行 PoC 脚本。
*   执行 `xelatex` + `bibtex` 生成最终版 PDF。
