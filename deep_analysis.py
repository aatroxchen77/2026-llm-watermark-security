import json
import numpy as np
from collections import Counter
from scipy.special import rel_entr
from transformers import AutoTokenizer

"""
水印侧信道泄漏分析工具 (Cryptographic Deep Analysis)
本脚本从密码学角度量化水印对模型原生分布的改变量。
核心指标：
1. KL 散度 (Kullback-Leibler Divergence): 量化统计不可区分性的偏离程度。
2. 全变差距离 (Total Variation Distance): 衡量两个概率分布之间的最大差异。
3. 侧信道泄漏点识别: 找出受水印算法偏置最严重的 Token。
"""

def calculate_kl_divergence(p, q):
    """计算两个概率分布之间的 KL 散度。"""
    p = np.array(p)
    q = np.array(q)
    # 过滤零值以避免无穷大
    mask = (p > 0) & (q > 0)
    return np.sum(rel_entr(p[mask], q[mask]))

def deep_analysis():
    results_file = 'experiment_results.jsonl'
    data = []
    # 读取实验生成的 JSONL 原始数据
    with open(results_file, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    # 加载本地分词器用于频率分析
    MODEL_PATH = '/data1/cyt/models/facebook--opt-1.3b'
    print(f"Loading tokenizer from {MODEL_PATH} for frequency modeling...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    except Exception as e:
        print(f"Failed to load tokenizer, falling back to simple split: {e}")
        tokenizer = None

    def get_distribution(texts):
        """对给定文本集合进行词频统计并归一化为概率分布。"""
        all_tokens = []
        for text in texts:
            if tokenizer:
                tokens = tokenizer.encode(text)
            else:
                tokens = text.lower().split()
            all_tokens.extend(tokens)
        
        counts = Counter(all_tokens)
        total = sum(counts.values())
        return counts, total

    baseline_texts = [d['baseline_text'] for d in data]
    watermarked_texts = [d['watermarked_text'] for d in data]

    print("Analyzing Indistinguishability (IND)...")
    cnt_n, total_n = get_distribution(baseline_texts)
    cnt_w, total_w = get_distribution(watermarked_texts)

    # 对齐词表以计算散度
    all_vocab = set(cnt_n.keys()) | set(cnt_w.keys())
    p_n = []
    p_w = []
    
    # 追踪侧信道泄漏 (泄漏 delta 最大的 Token)
    leaks = []

    # 使用 Laplace 平滑处理稀疏词表
    vocab_size = len(all_vocab)
    for token in all_vocab:
        prob_n = (cnt_n.get(token, 0) + 1) / (total_n + vocab_size)
        prob_w = (cnt_w.get(token, 0) + 1) / (total_w + vocab_size)
        p_n.append(prob_n)
        p_w.append(prob_w)
        
        # 计算该 Token 的偏置增量
        diff = abs(prob_w - prob_n)
        leaks.append((token, diff, prob_n, prob_w))

    kl_div = calculate_kl_divergence(p_w, p_n)
    tvd = 0.5 * np.sum(np.abs(np.array(p_w) - np.array(p_n)))
    
    # 对泄漏点按偏差强度排序
    leaks.sort(key=lambda x: x[1], reverse=True)
    top_leaks = leaks[:10]

    print("Analyzing Channel Robustness...")
    retention_rates = []
    for d in data:
        if d['z_watermarked'] > 0:
            # 鲁棒性指标：攻击后 Z-score 的保留比例
            rate = d['z_paraphrased'] / d['z_watermarked']
            retention_rates.append(rate)
    
    avg_retention = np.mean(retention_rates)

    # 构造度量汇总字典
    summary = {
        "kl_divergence": kl_div,
        "statistical_distance": tvd,
        "avg_z_retention_rate": avg_retention,
        "top_vulnerable_tokens": []
    }

    # 打印可视化报表
    print("\n" + "="*50)
    print("CRYPTOGRAPHIC DEEP ANALYSIS SUMMARY")
    print("="*50)
    print(f"KL Divergence (D_KL(Pw||Pn)): {kl_div:.6f}")
    print(f"Total Variation Distance (TVD): {tvd:.6f}")
    print(f"Average Z-score Retention (Robustness): {avg_retention:.2%}")
    
    print("\nTop 5 Vulnerable Tokens (Side-channel Leakage):")
    for token, diff, pn, pw in top_leaks[:5]:
        token_str = tokenizer.decode([token]) if tokenizer and isinstance(token, int) else token
        token_repr = token_str.replace('\n', '\\n') # 转义换行符便于观察
        print(f"  Token: '{token_repr:5}' | Bias Delta: {diff:.6e} (Base: {pn:.4f}, W: {pw:.4f})")
        summary["top_vulnerable_tokens"].append({"token": str(token_repr), "delta": diff})

    # 保存指标到 JSON 文件
    with open('cryptographic_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4)
    print(f"\n[Success] Analysis metrics saved to: cryptographic_metrics.json")

if __name__ == "__main__":
    deep_analysis()
