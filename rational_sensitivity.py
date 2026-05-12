"""
理性博弈者敏感性分析 (R6)
在不同替换率下测试定向攻击 vs 随机替换的效果，
生成消融曲线图。
"""
import json
import os
import random
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# CJK 字体
for _f in ['/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
           'C:\\Windows\\Fonts\\msyh.ttc']:
    if os.path.exists(_f):
        fm.fontManager.addfont(_f)
        plt.rcParams['font.family'] = fm.FontProperties(fname=_f).get_name()
        break
from core_classes import WatermarkEvaluator
from transformers import AutoTokenizer


MODEL_DIR = '/data1/cyt/models/'
GEN_MODEL = MODEL_DIR + 'facebook--opt-1.3b'
DEVICE = 'cuda:1' if torch.cuda.is_available() else 'cpu'
RESULTS_FILE = 'experiment_results.jsonl'
SAVE_PATH = 'report/rational_sensitivity.png'

# 高泄漏 Token 替换映射 (与 rational_attack_poc.py 一致)
ATTACK_MAPPING = {
    "\n": " ",
    " in": " within",
    " on": " upon",
    " The": " That",
    " of": " regarding",
}

# 随机替换使用的候选词
RANDOM_REPLACEMENTS = [" the", " and", " is", " to", " a", " it", " of", " in"]


def apply_targeted_attack(text, attack_mapping, rate, total_tokens):
    """
    定向攻击: 优先替换高泄漏 token 中的前 rate% 个。
    """
    if rate <= 0:
        return text
    num_to_replace = max(1, int(total_tokens * rate / 100))

    # 找出所有可替换位置 (字符级)
    candidates = []  # (char_pos, priority)
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

    # 按优先级排序 (高泄漏优先)
    candidates.sort(key=lambda x: x[1])

    # 限制数量
    selected = candidates[:num_to_replace]

    # 按位置逆序替换 (避免偏移)
    selected.sort(key=lambda x: x[0], reverse=True)
    result = text
    for pos, _, target, replacement in selected:
        result = result[:pos] + replacement + result[pos + len(target):]

    return result


def apply_random_attack(text, rate, total_tokens):
    """
    随机攻击: 随机替换 rate% 的 token 为常见词。
    """
    if rate <= 0:
        return text
    num_to_replace = max(1, int(total_tokens * rate / 100))

    # 分词找出可替换位置
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

    # 替换率扫描范围
    rates = list(range(0, 22, 2))  # 0%, 2%, ..., 20%

    # 存储结果: {rate: {'targeted': [z_scores], 'random': [z_scores]}}
    results = {r: {'targeted': [], 'random': []} for r in rates}

    # 为每条样本计算 Z-orig
    z_orig_list = [d['z_watermarked'] for d in data]

    print(f">>> Sweeping replacement rates on {len(data)} samples...")
    for i, (entry, z_orig) in enumerate(zip(data, z_orig_list)):
        wm_text = entry['watermarked_text']
        token_len = len(tokenizer.encode(wm_text))

        for rate in rates:
            # 定向攻击
            attacked_t = apply_targeted_attack(wm_text, ATTACK_MAPPING, rate, token_len)
            z_t = evaluator.compute_z_score(attacked_t, tokenizer)['z_score']
            results[rate]['targeted'].append(z_t)

            # 随机攻击
            attacked_r = apply_random_attack(wm_text, rate, token_len)
            z_r = evaluator.compute_z_score(attacked_r, tokenizer)['z_score']
            results[rate]['random'].append(z_r)

        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(data)} samples...")

    # 汇总
    print("\n" + "=" * 80)
    print(f"{'Replace Rate':>15} | {'Targeted Z (mean)':>18} | {'Random Z (mean)':>18} | {'Drop Diff':>10}")
    print("=" * 80)
    targeted_means = []
    random_means = []
    for rate in rates:
        t_mean = np.mean(results[rate]['targeted'])
        r_mean = np.mean(results[rate]['random'])
        targeted_means.append(t_mean)
        random_means.append(r_mean)
        diff = r_mean - t_mean
        print(f"{rate:>14d}% | {t_mean:>18.2f} | {r_mean:>18.2f} | {diff:>+10.2f}")
    print("=" * 80)

    # 画图
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(rates, targeted_means, 'o-', color='#D32F2F', linewidth=2, markersize=8,
            label='定向替换 (Targeted Attack)')
    ax.plot(rates, random_means, 's--', color='#757575', linewidth=2, markersize=8,
            label='随机替换 (Random Baseline)')
    ax.axhline(y=4.0, color='r', linestyle=':', alpha=0.7, linewidth=1.5,
               label='检测阈值 (Z=4.0)')
    ax.axhline(y=1.66, color='orange', linestyle=':', alpha=0.5, linewidth=1,
               label='原始 Rational Adv. 结果 (Z=1.66)')

    # 标注原始数据点
    orig_idx = rates.index(10) if 10 in rates else None
    if orig_idx is not None:
        ax.annotate(f'9.11% → Z={targeted_means[orig_idx]:.2f}',
                     xy=(10, targeted_means[orig_idx]),
                     xytext=(12, targeted_means[orig_idx] - 1.5),
                     arrowprops=dict(arrowstyle='->', color='#D32F2F'),
                     fontsize=10, color='#D32F2F')

    ax.set_xlabel('替换率 (Replacement Rate, %)', fontsize=12)
    ax.set_ylabel('平均 Z-score', fontsize=12)
    ax.set_title('理性博弈者攻击敏感性分析: 替换率 vs. 检测强度', fontsize=14)
    ax.legend(fontsize=10)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(SAVE_PATH, dpi=300)
    print(f"\n>>> Figure saved to {SAVE_PATH}")


if __name__ == "__main__":
    main()
