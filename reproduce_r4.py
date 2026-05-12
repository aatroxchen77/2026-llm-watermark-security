"""
R4 自相关分析全量复现 (CPU 兼容)
提取绿名单命中序列，计算 Lag-1 自相关系数，
验证 r1=0.0092, std=0.0606, 90% |r1|<0.1, Neff≈202。
"""
import json
import numpy as np
from transformers import AutoTokenizer
from watermark_processor import WatermarkDetector


def compute_lag1_autocorr(seq):
    if len(seq) < 10:
        return np.nan
    return np.corrcoef(seq[:-1], seq[1:])[0, 1]


def main():
    MODEL_DIR = '/data1/cyt/models/'
    GEN_MODEL = MODEL_DIR + 'facebook--opt-1.3b'

    print(">>> Loading data...")
    data = []
    with open('experiment_results.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    print(">>> Loading tokenizer and detector (CPU)...")
    tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
    detector = WatermarkDetector(
        vocab=list(tokenizer.get_vocab().values()),
        gamma=0.25,
        seeding_scheme='simple_1',
        device='cpu',
        tokenizer=tokenizer,
        ignore_repeated_bigrams=False,
    )

    autocorrs = []
    lengths = []

    print(f">>> Processing {len(data)} samples...")
    for i, entry in enumerate(data):
        text = entry['watermarked_text']
        try:
            result = detector.detect(text, return_green_token_mask=True, return_prediction=False)
            mask = result.get('green_token_mask', [])
        except Exception as e:
            print(f"  [{i}] Error: {e}")
            continue

        if len(mask) < 10:
            continue

        seq = np.array([1 if x else 0 for x in mask], dtype=float)
        r1 = compute_lag1_autocorr(seq)
        autocorrs.append(r1)
        lengths.append(len(seq))

        print(f"  [{i+1}/{len(data)}] T={len(seq)}, r1={r1:.4f}")

    autocorrs = np.array(autocorrs)
    autocorrs = autocorrs[~np.isnan(autocorrs)]

    print("\n" + "=" * 70)
    print("R4 自相关分析复现结果")
    print("=" * 70)
    print(f"  样本数:            {len(autocorrs)}")
    print(f"  平均文本长度:      {np.mean(lengths):.1f} tokens")
    print(f"  平均 Lag-1 自相关: {np.mean(autocorrs):.4f}")
    print(f"  自相关标准差:      {np.std(autocorrs):.4f}")
    print(f"  自相关中位数:      {np.median(autocorrs):.4f}")
    print(f"  自相关 95% CI:     [{np.percentile(autocorrs, 2.5):.4f}, {np.percentile(autocorrs, 97.5):.4f}]")
    print(f"  |r1| < 0.1 比例:   {np.mean(np.abs(autocorrs) < 0.1):.1%}")
    print(f"  |r1| < 0.2 比例:   {np.mean(np.abs(autocorrs) < 0.2):.1%}")

    mean_r1 = np.mean(autocorrs)
    mean_T = np.mean(lengths)
    neff = mean_T * (1 - mean_r1) / (1 + mean_r1)
    print(f"  有效样本量 Neff:   {neff:.0f} (名义 T = {mean_T:.0f})")

    print(f"\n>>> Verification:")
    print(f"  Paper: r1=0.0092  -> Computed: {mean_r1:.4f}")
    print(f"  Paper: std=0.0606 -> Computed: {np.std(autocorrs):.4f}")
    print(f"  Paper: 90% |r1|<0.1 -> Computed: {np.mean(np.abs(autocorrs) < 0.1):.1%}")
    print(f"  Paper: Neff≈202   -> Computed: {neff:.0f}")


if __name__ == "__main__":
    main()
