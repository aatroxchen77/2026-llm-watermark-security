"""
R6 敏感性曲线全量复现 (CPU 兼容)
输出 0-20% 替换率下定向替换和随机替换的 Z-score 均值，
用于与论文声称值对比验证。
"""
import json
import random
import numpy as np
from transformers import AutoTokenizer
from watermark_processor import WatermarkDetector


# 与 rational_sensitivity.py 一致的攻击映射
ATTACK_MAPPING = {
    "\n": " ",
    " in": " within",
    " on": " upon",
    " The": " That",
    " of": " regarding",
}

RANDOM_REPLACEMENTS = [" the", " and", " is", " to", " a", " it", " of", " in"]


def apply_targeted_attack(text, attack_mapping, rate, total_tokens):
    if rate <= 0:
        return text
    num_to_replace = max(1, int(total_tokens * rate / 100))
    candidates = []
    for priority, (target, replacement) in enumerate(attack_mapping.items()):
        idx = 0
        while True:
            idx = text.find(target, idx)
            if idx == -1:
                break
            candidates.append((idx, priority, target, replacement))
            idx += len(target)
    if not candidates:
        return text
    candidates.sort(key=lambda x: x[1])
    selected = candidates[:num_to_replace]
    selected.sort(key=lambda x: x[0], reverse=True)
    result = text
    for pos, _, target, replacement in selected:
        result = result[:pos] + replacement + result[pos + len(target):]
    return result


def apply_random_attack(text, rate, total_tokens):
    if rate <= 0:
        return text
    num_to_replace = max(1, int(total_tokens * rate / 100))
    words = list(text.split(' '))
    if len(words) <= 1:
        return text
    indices = random.sample(range(len(words)), min(num_to_replace, len(words)))
    for idx in indices:
        words[idx] = random.choice(RANDOM_REPLACEMENTS)
    return ' '.join(words)


def compute_green_z(text, tokenizer, detector):
    """直接使用 WatermarkDetector 计算 Z-score (无需 GPU)。"""
    try:
        result = detector.detect(text)
        return result['z_score']
    except Exception as e:
        print(f"    detect error: {e}")
        return None


def main():
    random.seed(42)
    np.random.seed(42)

    MODEL_DIR = '/data1/cyt/models/'
    GEN_MODEL = MODEL_DIR + 'facebook--opt-1.3b'

    print(">>> Loading data...")
    data = []
    with open('experiment_results.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    print(f">>> Loading tokenizer and detector (CPU)...")
    tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
    detector = WatermarkDetector(
        vocab=list(tokenizer.get_vocab().values()),
        gamma=0.25,
        seeding_scheme='simple_1',
        device='cpu',
        tokenizer=tokenizer,
    )

    rates = list(range(0, 22, 2))

    results = {r: {'targeted': [], 'random': []} for r in rates}

    print(f">>> Sweeping rates on {len(data)} samples...")
    for i, entry in enumerate(data):
        wm_text = entry['watermarked_text']
        token_len = len(tokenizer.encode(wm_text))

        for rate in rates:
            attacked_t = apply_targeted_attack(wm_text, ATTACK_MAPPING, rate, token_len)
            z_t = compute_green_z(attacked_t, tokenizer, detector)
            if z_t is not None:
                results[rate]['targeted'].append(z_t)

            attacked_r = apply_random_attack(wm_text, rate, token_len)
            z_r = compute_green_z(attacked_r, tokenizer, detector)
            if z_r is not None:
                results[rate]['random'].append(z_r)

        if (i + 1) % 5 == 0:
            print(f"  Processed {i+1}/{len(data)} samples...")

    # 输出结果
    print("\n" + "=" * 80)
    print(f"{'Replace Rate':>15} | {'Targeted Z (mean)':>20} | {'Random Z (mean)':>20} | {'Diff':>10}")
    print("=" * 80)
    for rate in rates:
        t_mean = np.mean(results[rate]['targeted']) if results[rate]['targeted'] else float('nan')
        r_mean = np.mean(results[rate]['random']) if results[rate]['random'] else float('nan')
        diff = r_mean - t_mean
        print(f"{rate:>14d}% | {t_mean:>20.2f} | {r_mean:>20.2f} | {diff:>+10.2f}")
    print("=" * 80)

    # 关键点验证
    print(f"\n>>> Verification against paper claims:")
    print(f"  10% targeted: {np.mean(results[10]['targeted']):.2f} (paper: 8.44)")
    print(f"  20% targeted: {np.mean(results[20]['targeted']):.2f} (paper: 8.39)")
    print(f"  20% random:   {np.mean(results[20]['random']):.2f} (paper: 6.68)")


if __name__ == "__main__":
    main()
