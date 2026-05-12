# Editorial Decision Package

## Part 1: Editorial Decision Letter

Dear Author(s),

Thank you for submitting your manuscript titled **"基于密码学伪随机词表划分的自回归语言模型水印安全性与鲁棒性深度研究报告"** to **IEEE Transactions on Information Forensics & Security (TIFS)**. Your manuscript has been reviewed by 4 independent reviewers plus the Editor-in-Chief and a Devil's Advocate.

### Decision: Major Revision

---

### Consensus Analysis

#### Synthesized Review Matrix

| Dimension | EIC (Conf: 4) | R1 — Methodology (Conf: 5) | R2 — Domain (Conf: 5) | R3 — Game Theory (Conf: 4) |
|-----------|:---:|:---:|:---:|:---:|
| **Overall Recommendation** | Major Revision | Major Revision | Major Revision | Major Revision |
| **Core Contribution** | TVD + Rational Adversary | DSC modeling + IND framing | Clean reproduction architecture | Game-theoretic adversary framing |
| **Primary Concern** | Lack of formal security definitions | Unvalidated IID assumptions | Incomplete literature review | Incomplete game-theoretic treatment |
| **Secondary Concern** | Overclaiming in title/abstract | No confidence intervals on any metric | Overclaiming on novelty | No equilibrium analysis |

---

#### [CONSENSUS-4] — Unanimous Agreement (All 4 Reviewers)

The following issues were independently identified by ALL reviewers. These MUST be addressed for the paper to be considered further:

**C4-1: Statistical uncertainty is completely absent.** Every quantitative claim in the paper — Z-score 9.92, TVD 0.2809, KL 0.251, detection rates 100%/92.5%/12.0% — is reported as a point estimate without confidence intervals, bootstrap uncertainty, or standard errors. For a paper making statistical security claims, this is a critical methodological gap. (EIC §Q5, R1 §W2, R2 §W3, R3 §Minor)

**C4-2: IID violation is acknowledged but unaddressed.** The paper correctly identifies that the Z-test's IID assumption is violated by serial correlation in autoregressive generation (§3.2), then proceeds to use the Z-test for all subsequent analysis without correction. Empirical autocorrelation should be reported, and the effective sample size should be computed. (R1 §W1, R2 §W4, DA §MAJOR-#3 ground, R3 §Minor)

**C4-3: Experimental scope is too narrow for the claims made.** Results are drawn from a single generator (OPT-1.3B), a single paraphraser (T5 Paraphrase-PAWS), a single watermark configuration (fixed γ, δ), and 100 prompts. Claims about "general robustness" or "scheme insecurity" require broader evaluation across models, paraphrasing strategies, and parameter settings. (EIC §W2, R1 §W4, R2 §W3, R3 §W2)

**C4-4: Literature review is severely incomplete.** The paper cites only 3 references (Kirchenbauer 2023a/b, Christ 2023, Mitchell 2023). Essential missing works include: Aaronson (2023, gumbel watermark), Kuditipudi et al. (2023, certified robustness), Wu et al. (2023, unbiased watermark), Zhao (2024, gamma watermark), Zhang et al. (2023, cryptographic framework), Fernandez et al. (2023, TVD leakage for diffusion models), and Hou et al. (2024, semantic watermark). (R2 §W1, all reviewers' context)

**C4-5: The paper's framing overclaims relative to its content.** The title promises "deep cryptographic security analysis," but the paper delivers an empirical reproduction with a simple TVD computation and a heuristic adversary demonstration. No formal security definitions, security games, or provable security bounds are provided. The abstract claims to "first propose the Rational Adversary model," but constrained-optimization formulations of watermark attacks appear in prior work. (EIC §W1, R2 §W2, DA §CRITICAL-#1)

---

#### [CONSENSUS-3] — Strong Majority

**C3-1: Rational Adversary attack implementation is under-specified.** Three reviewers (R1, R2, R3) agree that the attack (Section 6.2) is presented as a solution to a constrained optimization problem but implemented as a heuristic top-5 token replacement. Missing: sensitivity analysis over replacement rate, comparison with random baseline, and formal connection between TVD and attack success. R3 specifically notes the absence of regret analysis. (R1 §W4, R2 §Q3, R3 §W5)

**C3-2: TVD analysis conflates token-level and sequence-level indistinguishability.** Three reviewers (R1, R2, DA) identify this issue from different angles. R1 calls it "token-level vs. sequence-level IND conflation." R2 notes the TVD is computed on marginal frequencies, not conditional on context. DA argues that the leap from "TVD > 0" to "breakable" is a logical non sequitur under standard cryptographic IND definitions. (R1 §W3, R2 §Q5, DA §CRITICAL-#1)

---

#### [DA-CRITICAL] — Devil's Advocate Critical Issues

The following CRITICAL issues were identified by the Devil's Advocate. The Editorial Board has reviewed each:

**DA-C1: TVD = 0.28 does not imply IND breakage.** DA argues that the paper commits a category error: aggregate population-level TVD over the full vocabulary (0.28 / ~50,000 tokens ≈ 5.6×10⁻⁶ per token) does not translate to a sample-level distinguishing advantage for a PPT adversary observing a single T≈200 text. The paper never plays the IND security game.
- **Corroboration**: R1 §W3 and R2 §Q5 independently raise related concerns about the TVD→security leap.
- **Editorial Assessment**: **UPHELD.** The paper must either play the proper IND game and report distinguishing advantage, or explicitly caveat what the marginal TVD does and does not imply.

**DA-C2: Rational Adversary assumes maximal attacker knowledge.** DA argues the attack assumes the adversary knows: the watermark algorithm, the model, the hyperparameters, and the per-token leakage values. The paper does not evaluate gray-box or black-box variants. The 12% detection rate is therefore a worst-case bound, not a realistic threat assessment.
- **Corroboration**: R3 §W3 independently notes the adversarial cost model is under-specified.
- **Editorial Assessment**: **UPHELD.** The paper must either evaluate the adversary under more restrictive threat models or acknowledge the limitation prominently.

**DA-C3: DSC model validation is circular.** DA argues that the DSC model fits p ≈ 0.225 from the empirical Z-scores (Z_orig=9.92, Z_att=5.45) and then "validates" the model by checking this p aligns with the 47.35% text retention rate — using the same data.
- **Corroboration**: No other reviewer raised this specific concern.
- **Editorial Assessment**: **PARTIALLY UPHELD.** The circularity is real but can be fixed: re-estimate p on a held-out subset and validate on the remaining data. The DSC model's value as a parsimonious analytic framework is still recognized.

---

#### [SPLIT] — Divided Opinion

**S-1: Severity of the literature gap.** R2 considers the incomplete literature review (only 3 citations) a fatal weakness that undermines the paper's credibility. EIC and R1 mention it as important but not crippling. Resolution: R2's domain expertise (Confidence: 5) merits full weight. The literature review must be substantially expanded.

**S-2: Role of the "Chinese language" barrier.** EIC flags that the paper is entirely in Chinese, which is unusual for IEEE TIFS. R1, R2, and R3 do not mention language. Resolution: This is a course report, not a journal submission. The language is appropriate for its academic context.

**S-3: Human evaluation necessity.** EIC calls for human evaluation of text quality. R1 and R2 do not mention it. DA observes that PPL differences (11.45→15.32) are within an acceptable range. Resolution: Human evaluation would strengthen the paper but is not a requirement for a course report. The paper should note this as a limitation.

---

### Decision Rationale

The Editorial Board has reached a consensus of **Major Revision**. The rationale is as follows:

1. **The paper addresses a legitimate and timely problem** — the tension between practical LLM watermark robustness and provable statistical security. The TVD leakage analysis, DSC channel model, and Rational Adversary framing are conceptually valuable and represent genuine analytical effort.

2. **However, the paper suffers from a consistent pattern of overclaiming relative to its content.** The title, abstract, and conclusion position the work as a formal cryptographic security analysis, but the actual contribution is an empirical reproduction with metric-based observations. This mismatch between framing and delivery is the paper's single most significant flaw.

3. **Every reviewer recommends Major Revision.** The Devil's Advocate has identified CRITICAL issues (DA-C1, DA-C2) that preclude Accept and require substantive response. Three of the four main reviewers (R1, R2, EIC) emphasize the need for formal security definitions or a recalibration of claims.

4. **The paper's strengths — the DSC model, the entropy analysis, the PPL-Z-score tradeoff visualization, the Dist-n diversity analysis — are real and should be preserved.** The revision should deepen these existing contributions rather than add new ones.

5. **The Decision is Major Revision rather than Reject** because the core contributions are salvageable. The experimental infrastructure is sound, the Rational Adversary concept is genuinely useful (even if under-developed), and the empirical findings are reproducible. The paper needs structural revision and content supplementation, not a fresh start.

---

### Summary of Key Issues

1. **Formal security framework**: The paper must either provide formal IND-style security definitions (security games, advantage bounds) or recalibrate its claims to match its empirical content. "Cryptographic" in the title must be justified or removed.

2. **Literature review**: Must expand from 3 to at least 10-15 references covering Aaronson (2023), Kuditipudi et al. (2023), Wu et al. (2023), Zhao (2024), Zhang et al. (2023), Fernandez et al. (2023), and others.

3. **Uncertainty quantification**: Every quantitative claim needs confidence intervals, bootstrap estimates, or standard errors.

4. **IID violation treatment**: The Z-test reliance must be justified with empirical autocorrelation analysis and effective sample sizes.

5. **Rational Adversary implementation**: Must include sensitivity analysis (0% to 20% replacement rate), comparison with random-replacement baseline, and discussion of threat model assumptions.

6. **TVD→security leap**: Must bridge the gap between aggregate TVD and sample-level distinguishing advantage, or explicitly limit what the TVD analysis claims.

---

## Part 2: Revision Roadmap

### Required Revisions (Must Fix — P1)

| # | Revision Item | Source(s) | Priority | Est. Effort |
|---|--------------|-----------|----------|-------------|
| R1 | **Recalibrate claims to match content**: Either introduce formal security definitions (IND-style games, advantage bounds) OR revise title/abstract to remove "cryptographic," "deep security analysis," and related overclaims. A middle ground: keep the security framing but explicitly state limitations. | EIC §W1, R2 §W2, DA §C1 | **P1** | 3-5 days |
| R2 | **Expand literature review**: Add Aaronson (2023), Kuditipudi et al. (2023), Wu et al. (2023), Zhao (2024), Zhang et al. (2023), Fernandez et al. (2023), Hou et al. (2024), and at least 5 additional references. Each must be integrated into the narrative, not just listed. | R2 §W1, EIC §W5 | **P1** | 2-3 days |
| R3 | **Add confidence intervals / uncertainty**: For all core metrics (Z-scores, TVD, KL, detection rates), report bootstrap confidence intervals or standard errors. At minimum: 95% CI for TVD, detection rate, and Z-score means. | R1 §W2, R2 §W3, EIC §Q5 | **P1** | 1-2 days |
| R4 | **Address IID violation empirically**: Report autocorrelation of green-list token sequence (Lag-1 autocorrelation, effective sample size). Justify Z-test robustness to the observed dependence, or switch to a robust alternative (block bootstrap, permutation test). | R1 §W1, R2 §W4, DA context | **P1** | 2-3 days |
| R5 | **Clarify the TVD→security argument**: Either (a) define the IND game, compute the distinguishing advantage from the empirical TVD, and report the sample complexity; or (b) explicitly state that TVD measures marginal distribution shift and does NOT imply computational IND breakage. | DA §C1, R1 §W3, R2 §Q5 | **P1** | 2-3 days |
| R6 | **Rational Adversary sensitivity analysis**: Provide ablation showing Z-score vs. % tokens replaced (0% to 20%, step 1%). Compare with random-replacement baseline. Discuss threat model assumptions (white-box vs. black-box). | R1 §W4, R3 §W5, DA §C2 | **P1** | 2-3 days |

### Suggested Revisions (Should Fix — P2)

| # | Revision Item | Source(s) | Priority | Est. Effort |
|---|--------------|-----------|----------|-------------|
| S1 | **Expand experimental scope**: Add at least one additional model (e.g., LLaMA-2-7B or GPT-2-XL) and one additional paraphrasing method. Note: if computational constraints prevent this, add as a prominent limitation. | EIC §W2, R2 §Q4 | **P2** | 3-5 days |
| S2 | **DSC cross-validation**: Re-estimate p on a held-out subset of prompts and validate the predicted Z_att on the remaining data. Report the cross-validated R² or MSE. | DA §C3 | **P2** | 1 day |
| S3 | **DSC model limitations acknowledged**: Explicitly state that the DSC model assumes independent/random flips and does not apply to a strategic (Rational) adversary. Separately model the rational adversary's non-uniform flipping. | R3 §W4, DA §MAJOR-#3 | **P2** | 1-2 days |
| S4 | **Compute η_adv**: The attack efficiency metric is defined but never computed. Report actual values for both T5 and Rational Adversary scenarios. | R3 §W5, DA §MINOR-#3 | **P2** | 0.5 day |
| S5 | **Parameter exploration (γ, δ)**: If possible, show how TVD and Z-score vary across at least 2-3 values of δ (bias strength). If not possible, add as a future work direction. | R1 §Q6, R3 §W2 | **P2** | 2-3 days |
| S6 | **Address DA's "perverse incentive" observation**: The Rational Adversary paradoxically improves PPL (15.32→13.04). Discuss this welfare implication. | R3 §Q5, DA §OBS | **P2** | 1 day |
| S7 | **Human evaluation note**: Add a limitations paragraph acknowledging the lack of human evaluation for text quality. If feasible, add a small-scale human study (e.g., 20 samples rated by 3 judges). | EIC §W4 | **P2** | 2-5 days |

### Minor Fixes (Nice to Fix — P3)

| # | Issue | Source(s) | Effort |
|---|-------|-----------|--------|
| M1 | Clarify "text retention" metric definition for both T5-attacked and Rational Adversary (currently conflates lexical overlap with semantic preservation) | R2 §Argument logic, DA §MINOR-#1 | 0.5 day |
| M2 | Specify logarithm base in KL divergence computation (nats vs. bits) | R1 §Minor | 0.25 day |
| M3 | Report whether Z-score 9.92 is mean, median, or max across 100 prompts | EIC §Minor | 0.25 day |
| M4 | Remove \textcolor{red} from Table 1 (biases reader interpretation) | R2 §Minor | 0.25 day |
| M5 | Define "risk level" in leakage token table with quantitative thresholds | R2 §Minor | 0.5 day |
| M6 | Add Durbin-Watson or Ljung-Box test for serial correlation in green-list indicator sequence | R3 §Minor | 0.5 day |
| M7 | Replace "Discrete Symmetric Channel" with more accurate terminology (or fully model the 2×2 transition matrix) | R2 §Minor | 0.5 day |

---

### Revision Checklist

#### Priority 1 — Structural Revisions (Estimated total effort: 12-19 days)
- [ ] R1: Recalibrate claims to match content (formalize or reframe)
- [ ] R2: Expand literature review (10-15+ references)
- [ ] R3: Add confidence intervals / uncertainty quantification
- [ ] R4: Address IID violation empirically
- [ ] R5: Clarify TVD→security argument
- [ ] R6: Rational Adversary sensitivity analysis + baseline

#### Priority 2 — Content Supplementation (Estimated total effort: 10-17 days)
- [ ] S1: Broaden experimental scope or add limitation
- [ ] S2: DSC cross-validation
- [ ] S3: Separate DSC model vs. rational adversary framing
- [ ] S4: Compute η_adv values
- [ ] S5: Parameter exploration or future work
- [ ] S6: Discuss perverse incentive observation
- [ ] S7: Add human evaluation or limitation

#### Priority 3 — Text and Formatting (Estimated total effort: 2-3 days)
- [ ] M1: Clarify text retention metric
- [ ] M2: Specify log base in KL divergence
- [ ] M3: Report Z-score statistic type (mean/median/max)
- [ ] M4: Remove \textcolor{red} from Table 1
- [ ] M5: Define risk level thresholds
- [ ] M6: Add serial correlation test
- [ ] M7: Rename DSC or model full matrix

---

### Revision Deadline

**Recommended: 6-8 weeks** (consistent with Major Revision for an archival journal)

---

### Response Letter Format

Please respond to each revision item using the following format:

> **Reviewer X / Item Y**: [original comment]
> **Author Response**: [how you addressed the comment, including specific changes made]
> **Change Location**: [section, page, line numbers]

For items you choose not to address, provide a clear justification.

---

## Part 3: Reviewer Report Summary (Appendix)

### EIC Report Summary
- **Recommendation**: Major Revision | **Confidence**: 4
- **Key Point**: The paper addresses a timely problem but lacks formal security definitions and overclaims. The TVD/Rational Adversary framing is valuable but needs deeper theoretical treatment.

### Reviewer 1 (Methodology) Summary
- **Recommendation**: Major Revision | **Confidence**: 5
- **Key Point**: Statistically the most rigorous review. Identifies the IID violation as the single most consequential methodological issue. Demands uncertainty quantification for all metrics and calls out the token-level vs. sequence-level IND conflation.

### Reviewer 2 (Domain) Summary
- **Recommendation**: Major Revision | **Confidence**: 5
- **Key Point**: Severest critic of literature coverage. Calls attention to 8+ missing essential references. Argues the paper's incremental contribution is modest and the positioning is inflated relative to delivery.

### Reviewer 3 (Perspective / Game Theory) Summary
- **Recommendation**: Major Revision | **Confidence**: 4
- **Key Point**: Most constructive in identifying cross-disciplinary opportunities. Recommends Stackelberg game framing, equilibrium analysis, and incentive-compatibility conditions. Raises the "perverse incentive" paradox where the adversary improves text quality.

### Devil's Advocate Summary
- **Recommendation**: N/A (DA does not provide recommendation)
- **Key Point**: 3 CRITICAL issues. The most damaging: the TVD→security logical leap (DA-C1) strikes at the paper's core thesis. Threat model assumptions for the Rational Adversary are unrealistically generous (DA-C2). DSC model validation is circular (DA-C3).
