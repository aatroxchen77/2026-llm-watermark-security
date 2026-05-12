"""
绿名单命中序列的自相关分析 (R4)
提取水印文本中每个 token 的红/绿归属序列，计算 Lag-1 自相关系数，
检验 IID 假设的偏离程度。
"""
import json
import numpy as np
import torch
from core_classes import WatermarkEvaluator
from transformers import AutoTokenizer


MODEL_DIR = '/data1/cyt/models/'
GEN_MODEL = MODEL_DIR + 'facebook--opt-1.3b'
DEVICE = 'cuda:1' if torch.cuda.is_available() else 'cpu'
RESULTS_FILE = 'experiment_results.jsonl'


def extract_green_sequence(text, evaluator, tokenizer):
    """提取文本的绿名单命中序列 (1=绿, 0=红)。"""
    # 直接使用 WatermarkDetector，传入 return_green_token_mask=True
    detector = evaluator._get_detector(tokenizer)  # 需要实现这个方法，或者直接创建 detector
    result = detector.detect(text, return_green_token_mask=True, return_prediction=False)
    mask = result.get('green_token_mask', [])
    return np.array([1 if x else 0 for x in mask])


def compute_lag1_autocorr(seq):
    """计算 Lag-1 自相关系数。"""
    if len(seq) < 10:
        return np.nan
    return np.corrcoef(seq[:-1], seq[1:])[0, 1]


def run_test_of_independence(seq):
    """
    对 IID 假设做简单检验: Ljung-Box 等价检验。
    若 p < 0.05 则拒绝 IID 假设。
    这里使用自相关的简单 z-test: z = sqrt(T) * r1 ~ N(0,1) under H0.
    """
    n = len(seq)
    r1 = compute_lag1_autocorr(seq)
    if np.isnan(r1):
        return None, None
    # Bartlett 近似: Var(r1) ≈ 1/n under H0
    z_stat = r1 * np.sqrt(n)
    # 双尾 p 值 (近似)
    from scipy.stats import norm
    p_value = 2 * norm.cdf(-abs(z_stat))
    return z_stat, p_value


def main():
    print(f">>> Loading environment (device={DEVICE})...")
    tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
    evaluator = WatermarkEvaluator(device=DEVICE, gamma=0.25)

    # 创建 detector 实例
    from watermark_processor import WatermarkDetector
    detector = WatermarkDetector(
        vocab=list(tokenizer.get_vocab().values()),
        gamma=0.25,
        seeding_scheme='simple_1',
        device=DEVICE,
        tokenizer=tokenizer,
        ignore_repeated_bigrams=False,
    )

    print(">>> Loading experiment data...")
    data = []
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    autocorrs = []
    z_stats_list = []
    p_vals_list = []
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

        n = len(seq)
        z_stat = r1 * np.sqrt(n)
        z_stats_list.append(z_stat)
        lengths.append(n)

        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(data)} samples...")

    # 汇总
    autocorrs = np.array(autocorrs)
    autocorrs = autocorrs[~np.isnan(autocorrs)]

    print("\n" + "=" * 70)
    print("绿名单命中序列 Lag-1 自相关分析结果")
    print("=" * 70)
    print(f"  样本数:            {len(autocorrs)}")
    print(f"  平均文本长度 (token): {np.mean(lengths):.1f}")
    print(f"  平均 Lag-1 自相关:   {np.mean(autocorrs):.4f}")
    print(f"  自相关标准差:        {np.std(autocorrs):.4f}")
    print(f"  自相关中位数:        {np.median(autocorrs):.4f}")
    print(f"  自相关 95% CI:      [{np.percentile(autocorrs, 2.5):.4f}, {np.percentile(autocorrs, 97.5):.4f}]")
    print(f"  |r1| < 0.1 比例:    {np.mean(np.abs(autocorrs) < 0.1):.1%}")
    print(f"  |r1| < 0.2 比例:    {np.mean(np.abs(autocorrs) < 0.2):.1%}")
    print()

    # 解释
    mean_r1 = np.mean(autocorrs)
    if abs(mean_r1) < 0.1:
        print("→ 平均自相关较弱 (< 0.1)，Z 检验的 IID 近似在长文本下较为合理。")
    elif abs(mean_r1) < 0.3:
        print("→ 平均自相关中等 (0.1-0.3)，建议使用有效样本量修正或 Block Bootstrap。")
    else:
        print("→ 平均自相关较强 (> 0.3)，Z 检验的显著性可能被显著高估，强烈建议使用稳健替代方案。")

    print("\n  有效样本量估计: Neff = T * (1 - r1) / (1 + r1)")
    neff = np.mean(lengths) * (1 - mean_r1) / (1 + mean_r1)
    print(f"  平均 Neff ≈ {neff:.0f} (名义 T = {np.mean(lengths):.0f})")


if __name__ == "__main__":
    main()
