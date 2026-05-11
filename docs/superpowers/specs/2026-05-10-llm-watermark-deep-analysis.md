# Design Spec: Phase 3 - Cryptographic Deep Analysis of LLM Watermarking

**Date:** 2026-05-10
**Topic:** Cryptographic Evaluation (IND, DSC, and Rational Adversary Game)
**Status:** Draft / Pending Review

## 1. Purpose
This phase transitions the evaluation from empirical NLP metrics to formal cryptographic proof-of-concepts. We aim to quantify the "Information Leakage" of the watermark using KL Divergence and model the "Attack Surface" as a noisy communication channel.

## 2. Core Analysis Modules

### 2.1 Indistinguishability (IND) Analysis
*   **Methodology:** Compute the Kullback-Leibler (KL) Divergence between the token distribution of Natural text ($P_n$) and Watermarked text ($P_w$).
*   **Goal:** Demonstrate the "Statistical Indistinguishability" of the watermark. If $D_{KL} \to 0$, the system is theoretically secure against frequency-based side-channel attacks.
*   **Implementation:** 
    *   Tokenize aggregate baseline and watermarked corpora.
    *   Compute relative frequencies across the top-K vocabulary.
    *   Calculate $D_{KL}(P_w || P_n)$.

### 2.2 Channel Capacity & DSC Modeling
*   **Concept:** Treat the Watermark Generator as a Transmitter and the T5-Attacker as a Noisy Discrete Symmetric Channel (DSC).
*   **Metric:** Z-score Retention Rate ($R = Z_{attacked} / Z_{original}$).
*   **Goal:** Estimate the "Channel Capacity" (threshold of noise/paraphrasing) before the cryptographic signal (Z > 4.0) is lost.
*   **Link to Theory:** Map the T5 semantic edit distance to a "Bit Error Rate" in a traditional communication system.

### 2.3 Rational Adversary Game (Theoretical)
*   **Simulation:** Identify "Vulnerable Tokens" (those with highest frequency delta after watermarking).
*   **Discussion:** Model a "Rational Adversary" who targets these specific tokens for substitution. Analyze the tradeoff between "Detection Evasion" and "Semantic Preservation".

## 3. Data Flow
1.  `experiment_results.jsonl` (from Phase 2) -> **`deep_analysis.py`**
2.  Output: `cryptographic_metrics.json` + `indistinguishability_plot.png`.

## 4. Success Criteria for Phase 3
1.  **Quantified IND:** Establish whether the scheme satisfies the Negligible Statistical Distance criterion.
2.  **Robustness Boundary:** Identify the maximum "Noise Level" (paraphrase intensity) the watermark can survive.
3.  **Theoretic Depth:** Provide the necessary mathematical grounding for the "30% Argumentation" score.
