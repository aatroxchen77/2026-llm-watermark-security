import json
import numpy as np
from collections import Counter
from scipy.special import rel_entr
from transformers import AutoTokenizer

def calculate_kl_divergence(p, q):
    """Calculate KL divergence between two probability distributions."""
    p = np.array(p)
    q = np.array(q)
    # Filter out zeros to avoid infinity
    mask = (p > 0) & (q > 0)
    return np.sum(rel_entr(p[mask], q[mask]))

def deep_analysis():
    results_file = 'experiment_results.jsonl'
    data = []
    with open(results_file, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    # Load a general tokenizer for frequency analysis (using OPT for consistency if possible)
    # If internet is slow, this might take a second.
    print("Loading tokenizer for frequency analysis...")
    try:
        tokenizer = AutoTokenizer.from_pretrained('facebook/opt-1.3b')
    except:
        print("Fallback to simple split because of network...")
        tokenizer = None

    def get_distribution(texts):
        all_tokens = []
        for text in texts:
            if tokenizer:
                tokens = tokenizer.encode(text)
            else:
                tokens = text.lower().split()
            all_tokens.extend(tokens)
        
        counts = Counter(all_tokens)
        total = sum(counts.values())
        # Return top 1000 for efficiency
        top_tokens = counts.most_common(1000)
        return counts, total

    baseline_texts = [d['baseline_text'] for d in data]
    watermarked_texts = [d['watermarked_text'] for d in data]

    print("Analyzing Indistinguishability...")
    cnt_n, total_n = get_distribution(baseline_texts)
    cnt_w, total_w = get_distribution(watermarked_texts)

    # Align vocabularies for KL divergence
    all_vocab = set(cnt_n.keys()) | set(cnt_w.keys())
    p_n = []
    p_w = []
    
    # Track top leaks (vulnerable tokens)
    leaks = []

    for token in all_vocab:
        prob_n = (cnt_n.get(token, 0) + 1) / (total_n + len(all_vocab)) # Laplace smoothing
        prob_w = (cnt_w.get(token, 0) + 1) / (total_w + len(all_vocab))
        p_n.append(prob_n)
        p_w.append(prob_w)
        
        diff = abs(prob_w - prob_n)
        leaks.append((token, diff, prob_n, prob_w))

    kl_div = calculate_kl_divergence(p_w, p_n)
    
    # Sort leaks
    leaks.sort(key=lambda x: x[1], reverse=True)
    top_leaks = leaks[:10]

    print("\nAnalyzing Channel Robustness...")
    retention_rates = []
    for d in data:
        if d['z_watermarked'] > 0:
            rate = d['z_paraphrased'] / d['z_watermarked']
            retention_rates.append(rate)
    
    avg_retention = np.mean(retention_rates)

    # Report
    summary = {
        "kl_divergence": kl_div,
        "statistical_distance": 0.5 * np.sum(np.abs(np.array(p_w) - np.array(p_n))), # Total Variation Distance
        "avg_z_retention_rate": avg_retention,
        "top_vulnerable_tokens": []
    }

    print("\n" + "="*50)
    print("CRYPTOGRAPHIC DEEP ANALYSIS SUMMARY")
    print("="*50)
    print(f"KL Divergence (D_KL(Pw||Pn)): {kl_div:.6f}")
    print(f"Total Variation Distance (TVD): {summary['statistical_distance']:.6f}")
    print(f"Average Z-Retention (Robustness): {avg_retention:.2%}")
    
    print("\nTop 5 Vulnerable Tokens (Side-channel Leakage):")
    for token, diff, pn, pw in top_leaks[:5]:
        token_str = tokenizer.decode([token]) if tokenizer and isinstance(token, int) else token
        print(f"  Token: '{token_str}' | Bias Delta: {diff:.6e} (Base: {pn:.4f}, W: {pw:.4f})")
        summary["top_vulnerable_tokens"].append({"token": str(token_str), "delta": diff})

    with open('cryptographic_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4)
    print("\nDetailed metrics saved to cryptographic_metrics.json")

if __name__ == "__main__":
    deep_analysis()
