# Implementation Plan: LLM Watermarking Robustness & Naturalness Evaluation

**Date:** 2026-05-10
**Based on Spec:** `2026-05-10-llm-watermark-experiment-design.md`
**Target Environment:** Biolab Server (`biolab`), `watermark` Conda Environment

## 1. Phase 1: Setup & Model Preparation

### 1.1 Model Acquisition
Use the `hfd.sh` script on the biolab server to download missing models to `/data1/cyt/models/`.
*   **Attack Model:** `Vamsi/T5_Paraphrase_Puzzler` (T5-base-paraphraser).
*   **Evaluation Model:** `gpt2-large`.
*   **Verify Local Model:** Ensure `facebook/opt-1.3b` is accessible at `/data1/cyt/models/facebook--opt-1.3b`.

### 1.2 Environment Verification
*   Activate the environment: `conda activate watermark`.
*   Verify required packages: `torch`, `transformers`, `nltk`, `scipy`, `numpy`, `pandas`.

---

## 2. Phase 2: Core Class Implementation

### 2.1 `WatermarkGenerator` (Modular wrapper)
*   **Location:** `experiments/generation.py`
*   **Responsibilities:**
    *   Initialize `OPT-1.3b`.
    *   Integrate `WatermarkLogitsProcessor` from `watermark_processor.py`.
    *   Implement a `generate_pair` method:
        *   Takes a prompt.
        *   Generates **Baseline** (no logit biasing).
        *   Generates **Watermarked** ($\gamma=0.25, \delta=2.0$).
        *   Returns a dictionary with both outputs and metadata (entropy tag).
    *   **Constraint:** Ensure generated text (excluding prompt) has a minimum length of 200 tokens.

### 2.2 `WatermarkAttacker` (Robustness)
*   **Location:** `experiments/attack.py`
*   **Responsibilities:**
    *   Initialize `T5-base-paraphraser`.
    *   Implement `paraphrase` method:
        *   Takes watermarked text.
        *   Runs T5 rewriting.
        *   Returns the paraphrased version.

### 2.3 `WatermarkEvaluator` (Quality & Detection)
*   **Location:** `experiments/evaluation.py`
*   **Responsibilities:**
    *   Initialize `WatermarkDetector` and `GPT2-Large`.
    *   **PPL Calculation:** Implement `compute_ppl` using `GPT2-Large`. 
        *   *Tip:* Ensure proper tokenizer alignment (GPT2 tokenizer must handle the input IDs correctly for its own loss calculation).
    *   **Z-score Distribution:** Run `detector.detect` on Baseline, Watermarked, and Paraphrased text.
    *   **Diversity Metrics:** Compute Self-BLEU and Dist-n.

---

## 3. Phase 3: Pipeline Orchestration

### 3.1 `run_pipeline.py` (Main Entry)
*   **Memory Management:** Implement a sequential "Load-Process-Unload" strategy to fit within 24GB VRAM.
    1.  **Step 1 (Generation):** Load OPT, generate all pairs, save to `raw_results.jsonl`, delete OPT and clear cache.
    2.  **Step 2 (Attack):** Load T5, paraphrase watermarked samples, save to `attacked_results.jsonl`, delete T5 and clear cache.
    3.  **Step 3 (Evaluation):** Load GPT2-Large, evaluate all three versions (Baseline, Watermarked, Paraphrased), save to `final_results.jsonl`.
*   **Entropy Separation:** Prompts should be categorized into "High Entropy" (creative) and "Low Entropy" (factual/technical) groups during generation to allow for stratified analysis.

---

## 4. Phase 4: Data Management & Reporting

### 4.1 Output Formats
*   **JSONL Logging:** Save full results at each stage to prevent data loss on crash.
    *   Fields: `prompt_id`, `prompt`, `entropy_type`, `baseline_text`, `watermarked_text`, `paraphrased_text`, `z_scores`, `ppl_scores`, `diversity`.
*   **Summary CSV:** Generate a flat table for easy plotting in R/Python.

### 4.2 Visualization
*   Create a script `experiments/visualize.py`:
    *   Histograms of Z-scores (Baseline vs. Watermarked vs. Paraphrased).
    *   PPL vs. Z-score scatter plot (Naturalness-Robustness Trade-off).
    *   Bar charts comparing high/low entropy performance.

---

## 5. Timeline (Estimated)
1.  **Day 1:** Setup, Model Download, and `WatermarkGenerator` implementation.
2.  **Day 2:** `WatermarkAttacker` and `WatermarkEvaluator` (PPL logic).
3.  **Day 3:** Pipeline integration, first full run on biolab server.
4.  **Day 4:** Analysis, visualization, and report finalization.
