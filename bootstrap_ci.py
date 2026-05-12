"""
Bootstrap 置信区间分析 (R3)
对实验数据中的核心指标进行 Bootstrap 重采样，计算 95% CI。
"""
import json
import numpy as np
from collections import defaultdict


def load_data(file_path='experiment_results.jsonl'):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def bootstrap_ci(values, n_resamples=10000, ci=95):
    """Bootstrap 重采样估计置信区间。"""
    values = np.array(values)
    means = []
    for _ in range(n_resamples):
        sample = np.random.choice(values, size=len(values), replace=True)
        means.append(np.mean(sample))
    lower = np.percentile(means, (100 - ci) / 2)
    upper = np.percentile(means, 100 - (100 - ci) / 2)
    return np.mean(values), lower, upper


def main():
    np.random.seed(42)
    data = load_data()

    metrics = {
        'Z-score (Baseline)':      [d['z_baseline'] for d in data],
        'Z-score (Watermarked)':   [d['z_watermarked'] for d in data],
        'Z-score (T5 Attacked)':   [d['z_paraphrased'] for d in data],
        'PPL (Baseline)':          [d['ppl_baseline'] for d in data],
        'PPL (Watermarked)':       [d['ppl_watermarked'] for d in data],
    }

    # 分层: 高熵 vs 低熵
    for entropy_type in ['high-entropy', 'low-entropy']:
        subset = [d for d in data if d.get('type') == entropy_type]
        metrics[f'Z (Watermarked, {entropy_type})'] = [d['z_watermarked'] for d in subset]

    print("=" * 80)
    print(f"{'Metric':<40} {'Mean':>10} {'95% CI':>24}")
    print("=" * 80)
    for name, values in metrics.items():
        mean, lo, hi = bootstrap_ci(values)
        print(f"{name:<40} {mean:>10.3f}  [{lo:>10.3f}, {hi:>10.3f}]")

    # 检测率 Bootstrap (准确率)
    print("\n" + "检测率 Bootstrap (阈值为 Z > 4.0):")
    for label, key in [('Baseline', 'z_baseline'), ('Watermarked', 'z_watermarked'),
                       ('T5 Attacked', 'z_paraphrased')]:
        detected = [1 if d[key] > 4.0 else 0 for d in data]
        _, lo, hi = bootstrap_ci(detected)
        mean = np.mean(detected)
        print(f"  {label:<20} {mean:>6.1%}  [{lo:>6.1%}, {hi:>6.1%}]")


if __name__ == "__main__":
    main()
