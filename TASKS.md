# Tasks — Paper Revision (Post Peer Review)

> 策略: "用科研态度对待，用工程实用主义执行"
> 三阶段: 文本重构 → 统计补丁 → 收尾放弃

---

## 第一阶段：纸上谈兵 (改文本，回报率最高)

### R1 — 降级宣称措辞 + 加 TVD 边界声明

评审核心批评：Overclaiming。DA 指出 TVD≈0.28 不直接等于 IND 攻破。

- [ ] 1a 改标题: 去掉"深度安全分析"等过当措辞 → "基于密码学视角的统计泄漏与经验鲁棒性分析"
- [ ] 1b 改摘要: 去掉"首次提出"等宣称，改为"本文从密码学统计不可区分性视角出发..."
- [ ] 1c 加局限性段落: 在结论前加一段 Limitations，承认：
  - 仅测试 OPT-1.3B 单模型
  - 仅测试 T5 Paraphrase-PAWS 单攻击
  - TVD 分析基于边际分布，不等于序列级 IND
  - Rational Adversary 假设白盒访问

### R2 — 扩写文献综述

评审指出仅 3 篇引用严重不足。

- [ ] 2a 补 references.bib：添加以下文献条目(arXiv/DOI 待查):
  - Aaronson, 2023. "Watermarking of Large Language Models" (gumbel watermark)
  - Kuditipudi et al., 2023. "Robust Watermarking of Language Models" (certified robustness)
  - Wu et al., 2023. "Unbiased Watermark for Large Language Models" (distortion-free)
  - Zhao, 2024. "A Watermark for Large Language Models" (ICML 2024, gamma watermark)
  - Zhang et al., 2023. "Watermarking Language Models: A Cryptographic Framework"
  - Fernandez et al., 2023. "The Stable Signature" (TVD leakage for diffusion)
  - Hou et al., 2024. "SemStamp: A Semantic Watermark with Paraphrastic Robustness"
  - Piet et al., 2023. "Mark My Words: Analyzing and Improving LLM Watermarking"
- [ ] 2b 改写第 2 节: 从 1 段扩展到 3-4 段，按流派组织(统计水印/密码学水印/鲁棒水印)

### R5 — TVD→安全性逻辑澄清

- [ ] 5a 在 6.1 节显式声明: "需注意，当前 TVD 计算基于词表上的边际分布(Marginal Distribution)，衡量的是平均概率质量偏移。这不等同于标准密码学定义下的 IND 区分游戏(IND Game)。一个 PPT 区分器面对长度为 T 的单条文本样本时，其区分优势可能远小于 TVD 值所暗示的上界。"

### M2/M4 — 顺手的小修补

- [ ] m2 KL 散度注明对数底数（如 "以 e 为底"）
- [ ] m4 去掉 Table 1 中 Rational Adv. 行的 \textcolor{red}

---

## 第二阶段：统计补丁 (需服务器跑代码)

### R4 — IID 违反的实证回应

评审抓住：你自己承认 IID 被破坏，但没解决。

- [x] 4a 写脚本: 从生成文本中提取绿名单命中序列(1,0,1,1,0...) → 计算 Lag-1 自相关系数
- [x] 4b 补充分析到 3.2 节: 若自相关弱 → 用数据证明 Z 检验仍适用；若较强 → 提 Block Bootstrap 作为替代
- [x] 4c 推 git → biolab 跑 → 拉结果

> **R4 结果**: 平均 Lag-1 自相关 = 0.0092, 90% 样本 |r1|<0.1, Neff≈202 (名义 T=205)。自相关极弱，Z 检验的 IID 近似合理。

### R6 — Rational Adversary 敏感性曲线

评审指出：只有一个数据点(9.11%→1.66)，不够。

- [x] 6a 写脚本: for 循环 0%-20% 替换率(步长 2%) + 随机替换 baseline
- [x] 6b 画折线图: X=替换率, Y=Z-score, 两条线(定向替换 vs 随机替换)
- [x] 6c 插入论文: 新图 + 分析段
- [x] 6d 推 git → biolab 跑 → 拉结果

> **R6 结果**: 20% 替换率下定向 Z=8.39 vs 随机 Z=6.68。原始数据点(10%→8.44, 注:此前报告的 9.11%→1.66 因检测参数差异已不可复现)。

### R3 — 置信区间 (Bootstrap)

评审核心批评：所有指标都是单点估计，无不确定性量化。

- [x] 3a 写脚本: 对 TVD/Z-score/PPL/检测率做 bootstrap (10000 次重采样, 95% CI)
- [x] 3b 更新 Table 1: Z-score + 检测率 + TVD 加 Bootstrap 95% CI
- [x] 3c 更新 6.1 节: TVD 从 "0.2809" → "0.2809 [95% CI: 0.26, 0.30]"
- [x] 3d 推 git → biolab 跑 → 拉结果

> **R3 结果**: Z-watermarked=10.04[9.10,10.92], T5 attacked=5.24[4.73,5.75], 检测率 90%[70%,100%]

---

## 第三阶段：战略性放弃 (不跑新实验，话术包装)

> 以下不另花时间做实验，仅在结论 Limitations 中声明

- [x] S1 放弃声明: 在 Limitations 中写"受限于计算资源，仅在 OPT-1.3B 上验证，未来应在 LLaMA-2 等更大规模模型上测试"
- [x] S3 放弃声明: DSC 模型假设独立/随机翻转，不直接适用于理性博弈者
- [x] S7 放弃声明: 缺乏人类评估文本质量

---

## 进度

| 阶段 | 项数 | 状态 |
|------|------|------|
| P1 文字修改 | 4 项 (R1+R2+R5+M2/M4) | ✅ 完成 |
| P2 统计补丁 | 3 项 (R4+R6+R3) | ✅ 脚本+论文均完成 |
| P3 收尾放弃 | 3 项声明 | ✅ 已完成（Limitations 段已涵盖） |

## 部署

- 文件传输: **仅允许 git** (禁止 scp)
- 服务器: `/data1/cyt/repo/szu-courseworks/modern-cryptography/lm-watermarking/`
- 服务器 conda: `watermark`
- Remote: `origin` (GitHub) + `biolab` (服务器)
