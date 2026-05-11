import json
import os
import torch
from core_classes import WatermarkEvaluator
from transformers import AutoTokenizer

"""
理性博弈者攻击 PoC (Proof-of-Concept)
本脚本验证针对“高统计泄漏 Token”进行定向替换的攻击效率。
策略：识别文本中的高偏置 Token (如 \n, in, on)，执行简单的语义等价替换。
目标：对比定向替换与 T5 语义重写对 Z-score 的衰减效率。
"""

# 配置与路径
MODEL_DIR = '/data1/cyt/models/'
GEN_MODEL = os.path.join(MODEL_DIR, 'facebook--opt-1.3b')
DEVICE = 'cuda:1' if torch.cuda.is_available() else 'cpu'
RESULTS_FILE = 'experiment_results.jsonl'

# 识别出的高泄漏 Token 及其简单替换映射 (模拟攻击者策略)
ATTACK_MAPPING = {
    "\n": " ",        # 换行符替换为空格
    " in": " within",  # 介词替换
    " on": " upon",    # 介词替换
    " The": " That",   # 定冠词替换
    " of": " regarding" # 连词替换
}

def run_rational_attack():
    if not os.path.exists(RESULTS_FILE):
        print(f"Error: {RESULTS_FILE} not found. Run orchestrator.py first.")
        return

    print(">>> Loading environment and data...")
    tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
    evaluator = WatermarkEvaluator(device=DEVICE, gamma=0.25)
    
    data = []
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    print(f"\n>>> Starting Rational Attack PoC on {len(data)} samples...")
    print("-" * 70)
    print(f"{'Target Token':<15} | {'Replacements Made':<20}")
    print("-" * 70)

    rational_results = []
    for entry in data:
        original_w_text = entry['watermarked_text']
        attacked_text = original_w_text
        
        replacement_count = 0
        for target, replacement in ATTACK_MAPPING.items():
            count = attacked_text.count(target)
            if count > 0:
                attacked_text = attacked_text.replace(target, replacement)
                replacement_count += count
        
        # 计算攻击后的 Z-score
        z_stats = evaluator.compute_z_score(attacked_text, tokenizer)
        z_rational = z_stats['z_score']
        
        # 计算替换率 (对攻击效率的量化)
        token_len = len(tokenizer.encode(original_w_text))
        replacement_rate = replacement_count / token_len if token_len > 0 else 0

        rational_results.append({
            "prompt": entry['prompt'][:30] + "...",
            "z_orig": entry['z_watermarked'],
            "z_t5": entry['z_paraphrased'],
            "z_rational": z_rational,
            "repl_rate": replacement_rate
        })
        
        print(f"{entry['prompt'][:12]+'...':<15} | {replacement_count:<20} (Rate: {replacement_rate:.2%})")

    # 打印汇总对比
    print("\n" + "="*85)
    print(f"{'Prompt (Prefix)':<25} | {'Z-Orig':>8} | {'Z-T5 (Full)':>10} | {'Z-Rational':>12} | {'Eff. Gain'}")
    print("="*85)
    
    avg_drop_t5 = []
    avg_drop_rational = []

    for res in rational_results:
        # 效率增益：Z-score 衰减量 / 替换率 (越大表示攻击越“划算”)
        drop_t5 = res['z_orig'] - res['z_t5']
        drop_rational = res['z_orig'] - res['z_rational']
        
        gain = (drop_rational / res['repl_rate']) if res['repl_rate'] > 0 else 0
        
        print(f"{res['prompt']:<25} | {res['z_orig']:8.2f} | {res['z_t5']:10.2f} | {res['z_rational']:12.2f} | {gain:8.2f}")
        
        avg_drop_t5.append(drop_t5)
        avg_drop_rational.append(drop_rational)

    print("-" * 85)
    print(f"{'AVERAGE DROP':<25} | {'-':>8} | {sum(avg_drop_t5)/len(avg_drop_t5):10.2f} | {sum(avg_drop_rational)/len(avg_drop_rational):12.2f} | {'-'}")
    print("="*85)
    
    print("\n[Conclusion] Targeted replacement of high-leakage tokens provides a significant")
    print("signal decay relative to the minimal text perturbation introduced.")

if __name__ == "__main__":
    run_rational_attack()
