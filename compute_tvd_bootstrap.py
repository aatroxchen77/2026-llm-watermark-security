"""
TVD Bootstrap CI — 复现 deep_analysis.py 方法论:
使用 OPT-1.3B tokenizer + Laplace 平滑，对 10 对文本 Bootstrap 10000 次。
"""
import json
import numpy as np
from collections import Counter
from transformers import AutoTokenizer


def load_data(file_path='experiment_results.jsonl'):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def compute_tvd(baseline_texts, watermarked_texts, tokenizer):
    """复现 deep_analysis.py 的 TVD 计算 (Laplace 平滑)。"""
    # 收集所有 token
    def get_token_ids(texts):
        ids = []
        for text in texts:
            ids.extend(tokenizer.encode(text))
        return ids

    b_ids = get_token_ids(baseline_texts)
    w_ids = get_token_ids(watermarked_texts)

    cnt_n = Counter(b_ids)
    cnt_w = Counter(w_ids)
    total_n = sum(cnt_n.values())
    total_w = sum(cnt_w.values())

    all_vocab = set(cnt_n.keys()) | set(cnt_w.keys())
    vocab_size = len(all_vocab)

    p_n = []
    p_w = []
    for token in all_vocab:
        prob_n = (cnt_n.get(token, 0) + 1) / (total_n + vocab_size)
        prob_w = (cnt_w.get(token, 0) + 1) / (total_w + vocab_size)
        p_n.append(prob_n)
        p_w.append(prob_w)

    p_n = np.array(p_n)
    p_w = np.array(p_w)
    tvd = 0.5 * np.sum(np.abs(p_w - p_n))
    return tvd


def bootstrap_tvd(baseline_texts, watermarked_texts, tokenizer,
                  n_resamples=10000, seed=42):
    np.random.seed(seed)
    n = len(baseline_texts)

    # 点估计
    point_est = compute_tvd(baseline_texts, watermarked_texts, tokenizer)

    # Bootstrap
    samples = np.zeros(n_resamples)
    for i in range(n_resamples):
        indices = np.random.choice(n, size=n, replace=True)
        b_sample = [baseline_texts[j] for j in indices]
        w_sample = [watermarked_texts[j] for j in indices]
        samples[i] = compute_tvd(b_sample, w_sample, tokenizer)

    lo = np.percentile(samples, 2.5)
    hi = np.percentile(samples, 97.5)

    return point_est, lo, hi, samples


def main():
    data = load_data()
    baseline_texts = [d['baseline_text'] for d in data]
    watermarked_texts = [d['watermarked_text'] for d in data]

    MODEL_PATH = '/data1/cyt/models/facebook--opt-1.3b'
    print(f"Loading tokenizer from {MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

    print(f">>> Bootstrap TVD on {len(data)} text pairs, 10000 resamples...")
    tvd, lo, hi, samples = bootstrap_tvd(
        baseline_texts, watermarked_texts, tokenizer)

    print(f"\n{'='*55}")
    print(f"TVD Bootstrap Results (OPT tokenizer + Laplace smoothing)")
    print(f"{'='*55}")
    print(f"  Point estimate:    {tvd:.4f}")
    print(f"  95% CI:            [{lo:.4f}, {hi:.4f}]")
    print(f"  Bootstrap mean:    {np.mean(samples):.4f}")
    print(f"  Bootstrap std:     {np.std(samples):.4f}")
    print(f"  Match 0.2809?      {'YES' if abs(tvd - 0.2809) < 0.001 else f'NO (diff={abs(tvd-0.2809):.4f})'}")

    # 输出可直接用于论文的格式化结果
    print(f"\n>>> Paper-ready:")
    print(f"    TVD = {tvd:.4f} [95% CI: {lo:.3f}, {hi:.3f}]")


if __name__ == "__main__":
    main()
