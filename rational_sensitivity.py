"""
理性博弈者敏感性分析 (R6) — 顶刊风格
在不同替换率下测试定向攻击 vs 随机替换的效果，
生成消融曲线图。保存 PDF + PNG。
"""
import json, os, random, sys
import numpy as np
import torch
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

# ── Publication style (matching visualize_results.py) ─────────────────────
OKABE_ITO = ['#E69F00', '#56B4E9', '#009E73', '#F0E442',
             '#0072B2', '#D55E00', '#CC79A7', '#000000']
NATURE_SINGLE_INCH = 89 / 25.4  # 3.50 inches

def setup_style():
    mpl.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans',
                            'WenQuanYi Micro Hei', 'SimHei'],
        'font.size': 7,
        'axes.labelsize': 8,
        'axes.titlesize': 8,
        'axes.linewidth': 0.5,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.axisbelow': True,
        'axes.prop_cycle': mpl.cycler(color=OKABE_ITO),
        'xtick.major.size': 3,
        'xtick.minor.size': 2,
        'xtick.major.width': 0.5,
        'xtick.labelsize': 7,
        'ytick.major.size': 3,
        'ytick.minor.size': 2,
        'ytick.major.width': 0.5,
        'ytick.labelsize': 7,
        'lines.linewidth': 1.5,
        'lines.markersize': 4,
        'legend.fontsize': 7,
        'legend.frameon': False,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.05,
        'figure.constrained_layout.use': True,
        'axes.unicode_minus': False,
    })

from core_classes import WatermarkEvaluator
from transformers import AutoTokenizer


MODEL_DIR = '/data1/cyt/models/'
GEN_MODEL = MODEL_DIR + 'facebook--opt-1.3b'
DEVICE = 'cuda:1' if torch.cuda.is_available() else 'cpu'
RESULTS_FILE = 'experiment_results.jsonl'
SAVE_BASE = 'report/rational_sensitivity'

# 高泄漏 Token 替换映射 (与 rational_attack_poc.py 一致)
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
    results = {r: {'targeted': [], 'random': []} for r in rates}
    z_orig_list = [d['z_watermarked'] for d in data]

    print(f">>> Sweeping replacement rates on {len(data)} samples...")
    for i, (entry, z_orig) in enumerate(zip(data, z_orig_list)):
        wm_text = entry['watermarked_text']
        token_len = len(tokenizer.encode(wm_text))

        for rate in rates:
            attacked_t = apply_targeted_attack(wm_text, ATTACK_MAPPING, rate, token_len)
            z_t = evaluator.compute_z_score(attacked_t, tokenizer)['z_score']
            results[rate]['targeted'].append(z_t)

            attacked_r = apply_random_attack(wm_text, rate, token_len)
            z_r = evaluator.compute_z_score(attacked_r, tokenizer)['z_score']
            results[rate]['random'].append(z_r)

        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(data)} samples...")

    # Summary table
    print("\n" + "=" * 80)
    print(f"{'Replace Rate':>15} | {'Targeted Z':>18} | {'Random Z':>18} | {'Drop Diff':>10}")
    print("=" * 80)
    targeted_means = []
    random_means = []
    for rate in rates:
        t_mean = np.mean(results[rate]['targeted'])
        r_mean = np.mean(results[rate]['random'])
        targeted_means.append(t_mean)
        random_means.append(r_mean)
        print(f"{rate:>14d}% | {t_mean:>18.2f} | {r_mean:>18.2f} | {r_mean - t_mean:>+10.2f}")
    print("=" * 80)

    # ── Figure ──
    setup_style()
    fig, ax = plt.subplots(figsize=(NATURE_SINGLE_INCH, 2.6))

    ax.plot(rates, targeted_means, 'o-', color=OKABE_ITO[5], linewidth=1.5,
            markersize=5, markerfacecolor='white', markeredgewidth=1.2,
            label='Targeted attack (biased tokens)')
    ax.plot(rates, random_means, 's--', color=OKABE_ITO[0], linewidth=1.5,
            markersize=5, markerfacecolor='white', markeredgewidth=1.2,
            label='Random replacement')

    ax.axhline(y=4.0, color=OKABE_ITO[5], linestyle=':', linewidth=0.8,
               alpha=0.7, label=r'Threshold $\tau=4.0$')

    # Annotate the 10% point
    idx10 = rates.index(10) if 10 in rates else None
    if idx10 is not None:
        ax.annotate(f'10% → Z={targeted_means[idx10]:.2f}',
                     xy=(10, targeted_means[idx10]),
                     xytext=(11, targeted_means[idx10] - 2.0),
                     arrowprops=dict(arrowstyle='->', color=OKABE_ITO[5], lw=0.8),
                     fontsize=6.5, color=OKABE_ITO[5])

    ax.set_xlabel('Replacement rate (%)')
    ax.set_ylabel('Detection Z-score')
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 12)
    ax.legend(fontsize=6.5)

    for ext in ['pdf', 'png']:
        path = f'{SAVE_BASE}.{ext}'
        fig.savefig(path, dpi=300)
        print(f"  ✓ {path}")
    plt.close(fig)
    print(">>> Done.")


if __name__ == "__main__":
    main()
