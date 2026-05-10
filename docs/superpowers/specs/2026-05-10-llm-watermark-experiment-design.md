# Design Spec: LLM Watermarking Robustness & Naturalness Evaluation

**Date:** 2026-05-10
**Topic:** LLM Watermarking Experiment Suite (Phase 2)
**Status:** Draft / Pending Review

## 1. Purpose
The objective of this project is to evaluate the watermarking scheme proposed by Kirchenbauer et al. (2023) across three critical dimensions: **Robustness** against model-based paraphrase attacks, **Naturalness** (text quality), and **Reliability** in low-entropy scenarios. This provides the empirical evidence required for the "Research" portion of the Modern Cryptography course.

## 2. Core Components

### 2.1 Generation & Watermarking Module
*   **Base Model:** `facebook/opt-1.3b` (Source: Local path `/data1/cyt/models/facebook--opt-1.3b`).
*   **Watermark Config:** $\gamma=0.25$, $\delta=2.0$, Seeding: `simple_1`.
*   **Logic:**
    *   Load model/tokenizer.
    *   Generate two versions for each prompt: Baseline (No Watermark) and Watermarked.
    *   Save to `raw_results.jsonl`.
*   **Prompt Sets:** 
    *   General (Creative writing).
    *   Structured (Technical descriptions, high-entropy vs. low-entropy).

### 2.2 Paraphrase Attack Module (Robustness)
*   **Attack Model:** `Vamsi/T5_Paraphrase_Puzzler` (from HuggingFace).
*   **Input:** `raw_results.jsonl`.
*   **Operation:** Apply model-based rewriting to the watermarked text to see if the statistical signal persists.
*   **Output:** `attacked_results.jsonl` (adds `paraphrased_text`).

### 2.3 Evaluation & Metrics Module
*   **Quality Judge:** `gpt2-large`.
*   **Metrics:**
    1.  **Z-score Distribution:** Computed for baseline, watermarked, and paraphrased text.
    2.  **Perplexity (PPL):** Computed using `gpt2-large` to compare baseline vs. watermarked quality.
    3.  **Diversity (Self-BLEU / Dist-n):** Measure if watermarking reduces the richness of the vocabulary.
*   **Final Output:** A summary CSV and basic plots (histograms/scatter plots).

## 3. Data Flow
1.  `prompts` -> **Generation** -> `raw_results.jsonl` (Baseline, Watermarked).
2.  `raw_results.jsonl` -> **Attack** -> `attacked_results.jsonl` (adds Paraphrased).
3.  `attacked_results.jsonl` -> **Metrics** -> `final_metrics.json` + `plots/`.

## 4. Resource Allocation (Biolab Server)
*   **Device:** Single NVIDIA RTX 3090 (24GB VRAM).
*   **Strategy:** Sequential execution to avoid OOM.
    *   Step 1: Load OPT-1.3B, generate, unload.
    *   Step 2: Load T5, paraphrase, unload.
    *   Step 3: Load GPT2-Large, evaluate PPL, unload.

## 5. Success Criteria
1.  **Watermarking works:** Average Z-score of watermarked text > 4.0.
2.  **Robustness verified:** Average Z-score of paraphrased text remains > 3.0 (or significantly higher than baseline).
3.  **Quality impact quantified:** Delta PPL between baseline and watermarked is minimal (e.g., < 15% increase).
