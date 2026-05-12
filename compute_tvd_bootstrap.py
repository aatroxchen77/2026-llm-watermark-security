"""
TVD Bootstrap CI 计算
通过对文本样本进行 Bootstrap 重采样，估计 TVD 的 95% 置信区间。
"""
import json
import numpy as np
from collections import Counter


def load_data(file_path='experiment_results.jsonl'):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def build_token_dist(texts):
    """从文本列表构建 token 频率分布。"""
    counter = Counter()
    total = 0
    for text in texts:
        tokens = text.split()
        counter.update(tokens)
        total += len(tokens)
    # 归一化为概率分布
    dist = {}
    for token, count in counter.items():
        dist[token] = count / total
    return dist, counter, total


def compute_tvd(dist1, dist2, all_tokens):
    """计算两个分布之间的 Total Variation Distance。"""
    tvd = 0.0
    for token in all_tokens:
        p1 = dist1.get(token, 0.0)
        p2 = dist2.get(token, 0.0)
        tvd += abs(p1 - p2)
    return tvd / 2.0


def bootstrap_tvd(baseline_texts, watermarked_texts, n_resamples=10000, seed=42):
    """Bootstrap TVD 的置信区间。"""
    np.random.seed(seed)
    n = len(baseline_texts)
    assert len(watermarked_texts) == n

    # 收集所有出现的 token
    all_tokens = set()
    for text in baseline_texts + watermarked_texts:
        all_tokens.update(text.split())
    all_tokens = list(all_tokens)

    # 点估计
    b_dist, _, _ = build_token_dist(baseline_texts)
    w_dist, _, _ = build_token_dist(watermarked_texts)
    point_estimate = compute_tvd(b_dist, w_dist, all_tokens)

    # Bootstrap
    tvd_samples = []
    for _ in range(n_resamples):
        indices = np.random.choice(n, size=n, replace=True)
        b_sample = [baseline_texts[i] for i in indices]
        w_sample = [watermarked_texts[i] for i in indices]
        b_d, _, _ = build_token_dist(b_sample)
        w_d, _, _ = build_token_dist(w_sample)
        tvd_samples.append(compute_tvd(b_d, w_d, all_tokens))

    tvd_samples = np.array(tvd_samples)
    lo = np.percentile(tvd_samples, 2.5)
    hi = np.percentile(tvd_samples, 97.5)

    return point_estimate, lo, hi, tvd_samples


def main():
    data = load_data()
    baseline_texts = [d['baseline_text'] for d in data]
    watermarked_texts = [d['watermarked_text'] for d in data]

    print(f">>> Computing TVD bootstrap on {len(data)} text pairs, 10000 resamples...")
    tvd, lo, hi, samples = bootstrap_tvd(baseline_texts, watermarked_texts)

    print(f"\nResults:")
    print(f"  TVD point estimate:      {tvd:.6f}")
    print(f"  TVD 95% CI:              [{lo:.6f}, {hi:.6f}]")
    print(f"  CI width:                {hi - lo:.6f}")
    print(f"  Bootstrap mean:          {np.mean(samples):.6f}")
    print(f"  Bootstrap std:           {np.std(samples):.6f}")

    # 验证: 基于 token 频率的 TVD (与 cryptographic_metrics.json 一致)
    print(f"\nVerification (should match cryptographic_metrics.json):")
    print(f"  TVD point ≈ 0.2809?      {'YES' if abs(tvd - 0.2809) < 0.001 else f'NO (diff={abs(tvd-0.2809):.4f})'}")


if __name__ == "__main__":
    main()
