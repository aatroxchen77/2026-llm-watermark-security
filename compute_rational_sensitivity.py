"""
理性博弈者敏感性分析 — 计算阶段（服务器 CUDA）
在不同替换率下测试定向攻击 vs 随机替换的效果，
结果存为 JSON，供 plot_rational_sensitivity.py 画图。
"""
import json, os, random
import numpy as np
import torch
from core_classes import WatermarkEvaluator
from transformers import AutoTokenizer


MODEL_DIR = '/data1/cyt/models/'
GEN_MODEL = MODEL_DIR + 'facebook--opt-1.3b'
DEVICE = 'cuda:1' if torch.cuda.is_available() else 'cpu'
RESULTS_FILE = 'experiment_results.jsonl'
OUTPUT_JSON = 'rational_sensitivity_results.json'

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


def main():
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    print(f">>> Loading environment (device={DEVICE})...")
    tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
    evaluator = WatermarkEvaluator(device=DEVICE, gamma=0.25)

    print(">>> Loading experiment data...")
    data = []
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    rates = list(range(0, 22, 2))
    # Store per-sample raw values for downstream statistical analysis
    results = {str(r): {'targeted': [], 'random': []} for r in rates}

    print(f">>> Sweeping replacement rates on {len(data)} samples...")
    for i, entry in enumerate(data):
        wm_text = entry['watermarked_text']
        token_len = len(tokenizer.encode(wm_text))

        for rate in rates:
            attacked_t = apply_targeted_attack(wm_text, ATTACK_MAPPING, rate, token_len)
            z_t = evaluator.compute_z_score(attacked_t, tokenizer)['z_score']
            results[str(rate)]['targeted'].append(float(z_t))

            attacked_r = apply_random_attack(wm_text, rate, token_len)
            z_r = evaluator.compute_z_score(attacked_r, tokenizer)['z_score']
            results[str(rate)]['random'].append(float(z_r))

        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(data)} samples...")

    # Compute summary statistics
    summary = {'rates': rates}
    for rate in rates:
        t_vals = np.array(results[str(rate)]['targeted'])
        r_vals = np.array(results[str(rate)]['random'])
        summary[str(rate)] = {
            'targeted_mean': float(np.mean(t_vals)),
            'targeted_std': float(np.std(t_vals)),
            'random_mean': float(np.mean(r_vals)),
            'random_std': float(np.std(r_vals)),
        }

    # Save full results
    output = {'summary': summary, 'per_sample': results}
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(output, f, indent=2)
    print(f">>> Results saved to {OUTPUT_JSON}")

    # Print summary table
    print("\n" + "=" * 80)
    print(f"{'Replace Rate':>15} | {'Targeted Z':>18} | {'Random Z':>18} | {'Drop Diff':>10}")
    print("=" * 80)
    for rate in rates:
        s = summary[str(rate)]
        print(f"{rate:>14d}% | {s['targeted_mean']:>18.2f} | {s['random_mean']:>18.2f} | {s['random_mean'] - s['targeted_mean']:>+10.2f}")
    print("=" * 80)
    print(">>> Done. Now run plot_rational_sensitivity.py locally to generate figures.")


if __name__ == "__main__":
    main()
