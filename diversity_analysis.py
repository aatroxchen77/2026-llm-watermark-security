"""
Diversity Analysis for Watermarked Text
Computes Distinct-n (Dist-1, Dist-2, Dist-3) to measure vocabulary richness.
Self-BLEU requires multiple generations per prompt and is left for future work.
"""
import json
import numpy as np
from collections import Counter
import os


def load_data(file_path='experiment_results.jsonl'):
    data = []
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def compute_dist_n(text, n):
    """Compute Distinct-n: unique n-grams / total n-grams"""
    tokens = text.lower().split()
    if len(tokens) < n:
        return 0.0
    ngrams = [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
    unique = len(set(ngrams))
    total = len(ngrams)
    return unique / total if total > 0 else 0.0


def main():
    data = load_data()
    if not data:
        return

    print("=" * 70)
    print("DIVERSITY ANALYSIS: Distinct-n (词汇丰富度)")
    print("=" * 70)
    print(f"{'Prompt':30} | {'Dist-1':>8} {'Dist-2':>8} {'Dist-3':>8} | ΔDist-1")
    print("-" * 70)

    results = {"baseline": {"dist1": [], "dist2": [], "dist3": []},
               "watermarked": {"dist1": [], "dist2": [], "dist3": []}}

    for entry in data:
        prompt_short = entry['prompt'][:28] + ".." if len(entry['prompt']) > 28 else entry['prompt']

        # Baseline
        b_d1 = compute_dist_n(entry['baseline_text'], 1)
        b_d2 = compute_dist_n(entry['baseline_text'], 2)
        b_d3 = compute_dist_n(entry['baseline_text'], 3)
        results["baseline"]["dist1"].append(b_d1)
        results["baseline"]["dist2"].append(b_d2)
        results["baseline"]["dist3"].append(b_d3)

        # Watermarked
        w_d1 = compute_dist_n(entry['watermarked_text'], 1)
        w_d2 = compute_dist_n(entry['watermarked_text'], 2)
        w_d3 = compute_dist_n(entry['watermarked_text'], 3)
        results["watermarked"]["dist1"].append(w_d1)
        results["watermarked"]["dist2"].append(w_d2)
        results["watermarked"]["dist3"].append(w_d3)

        delta = w_d1 - b_d1
        print(f"{prompt_short:30} | {b_d1:8.4f} {b_d2:8.4f} {b_d3:8.4f} | {delta:+8.4f}")

    # Averages
    print("-" * 70)
    for label in ["baseline", "watermarked"]:
        avg_d1 = np.mean(results[label]["dist1"])
        avg_d2 = np.mean(results[label]["dist2"])
        avg_d3 = np.mean(results[label]["dist3"])
        print(f"{'Avg ' + label:30} | {avg_d1:8.4f} {avg_d2:8.4f} {avg_d3:8.4f}")

    delta_avg = np.mean(results["watermarked"]["dist1"]) - np.mean(results["baseline"]["dist1"])
    print(f"{'Avg Δ (W - B)':30} | {delta_avg:+8.4f}")
    print("=" * 70)
    print("\n[Conclusion] A positive ΔDist-1 indicates richer vocabulary in watermarked text,")
    print("while a negative Δ indicates reduced diversity due to watermark biasing.")


if __name__ == "__main__":
    main()
