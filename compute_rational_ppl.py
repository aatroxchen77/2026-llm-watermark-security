"""
计算 Rational Adversary (10% 定向替换) 攻击后文本的 PPL。
"""
import json
import random
import numpy as np
from core_classes import WatermarkEvaluator
from transformers import AutoTokenizer


ATTACK_MAPPING = {
    "\n": " ",
    " in": " within",
    " on": " upon",
    " The": " That",
    " of": " regarding",
}


def apply_targeted_attack(text, attack_mapping, rate, total_tokens):
    """定向攻击: 优先替换高泄漏 token 中的前 rate% 个 (与 rational_sensitivity.py 一致)。"""
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


def main():
    MODEL_DIR = '/data1/cyt/models/'
    JUDGE_MODEL = MODEL_DIR + 'gpt2-large'
    GEN_MODEL = MODEL_DIR + 'facebook--opt-1.3b'

    random.seed(42)
    np.random.seed(42)

    print(">>> Loading data and models...")
    data = []
    with open('experiment_results.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
    evaluator = WatermarkEvaluator(device='cpu', gamma=0.25, judge_model_path=JUDGE_MODEL)

    ppl_wm_list = []
    ppl_rational_list = []

    print(f">>> Processing {len(data)} samples at 10% replacement rate...")
    for i, entry in enumerate(data):
        wm_text = entry['watermarked_text']
        token_len = len(tokenizer.encode(wm_text))

        attacked = apply_targeted_attack(wm_text, ATTACK_MAPPING, 10, token_len)
        if attacked == wm_text:
            attacked = apply_targeted_attack(wm_text, ATTACK_MAPPING, 20, token_len)

        ppl_wm = evaluator.compute_ppl(wm_text)
        ppl_att = evaluator.compute_ppl(attacked)
        ppl_wm_list.append(ppl_wm)
        ppl_rational_list.append(ppl_att)

        print(f"  [{i+1}/{len(data)}] PPL(wm)={ppl_wm:.2f}, PPL(rational)={ppl_att:.2f}, delta={ppl_att-ppl_wm:+.2f}")

    print(f"\n{'='*55}")
    print(f"RESULTS:")
    print(f"  Watermarked PPL mean:        {np.mean(ppl_wm_list):.2f}")
    print(f"  Rational Adv. (10%) PPL mean:{np.mean(ppl_rational_list):.2f}")
    print(f"  PPL increase:                {np.mean(ppl_rational_list)-np.mean(ppl_wm_list):+.2f}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
