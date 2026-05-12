"""
补算 T5 释义文本的 PPL 和文本留存率。
"""
import json
import numpy as np
from core_classes import WatermarkEvaluator


def compute_token_retention(original_text, attacked_text):
    """逐 token 留存率 (基于空格分词)。"""
    orig_tokens = original_text.split()
    att_tokens = attacked_text.split()
    if not orig_tokens:
        return 0.0
    # 简单 unigram overlap
    orig_set = set(orig_tokens)
    att_set = set(att_tokens)
    intersection = orig_set & att_set
    return len(intersection) / len(orig_set)


def compute_self_bleu_like(original_text, attacked_text):
    """Unigram precision (类似 BLEU-1 precision)。"""
    orig_tokens = original_text.split()
    att_tokens = attacked_text.split()
    if not att_tokens:
        return 0.0
    orig_counts = {}
    for t in orig_tokens:
        orig_counts[t] = orig_counts.get(t, 0) + 1
    matches = 0
    for t in att_tokens:
        if orig_counts.get(t, 0) > 0:
            matches += 1
            orig_counts[t] -= 1
    return matches / len(att_tokens)


def main():
    import os
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

    print(">>> Loading data and model...")
    data = []
    with open('experiment_results.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    MODEL_DIR = '/data1/cyt/models/'
    JUDGE_MODEL = MODEL_DIR + 'gpt2-large'
    evaluator = WatermarkEvaluator(device='cpu', gamma=0.25, judge_model_path=JUDGE_MODEL)

    ppl_paraphrased_list = []
    retention_list = []
    bleu_like_list = []

    print(f">>> Processing {len(data)} samples...")
    for i, entry in enumerate(data):
        ppl = evaluator.compute_ppl(entry['paraphrased_text'])
        ppl_paraphrased_list.append(ppl)

        ret = compute_token_retention(entry['watermarked_text'], entry['paraphrased_text'])
        retention_list.append(ret)

        bleu = compute_self_bleu_like(entry['watermarked_text'], entry['paraphrased_text'])
        bleu_like_list.append(bleu)

        print(f"  [{i+1}/{len(data)}] PPL={ppl:.2f}, token_retention={ret:.4f}, bleu1_prec={bleu:.4f}")

    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  T5 PPL mean:          {np.mean(ppl_paraphrased_list):.2f}")
    print(f"  T5 PPL std:           {np.std(ppl_paraphrased_list):.2f}")
    print(f"  Token retention mean: {np.mean(retention_list):.4f} ({np.mean(retention_list)*100:.2f}%)")
    print(f"  BLEU-1 precision mean:{np.mean(bleu_like_list):.4f} ({np.mean(bleu_like_list)*100:.2f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
