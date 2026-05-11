import os
import json
import torch
from core_classes import WatermarkGenerator, WatermarkAttacker, WatermarkEvaluator
from transformers import AutoTokenizer

"""
大模型水印实验编排器 (Orchestrator)
本脚本负责执行完整的水印实验流水线，包括：
1. 文本生成（含水印与无水印对照组）
2. 语义重写攻击（T5 Paraphrase）
3. 指标评估（Z-score, PPL）
"""

# 路径配置
MODEL_DIR = '/data1/cyt/models/'
GEN_MODEL = os.path.join(MODEL_DIR, 'facebook--opt-1.3b')
ATTACK_MODEL = os.path.join(MODEL_DIR, 'Vamsi--T5_Paraphrase_Paws')
JUDGE_MODEL = os.path.join(MODEL_DIR, 'gpt2-large')

# 核心参数
GAMMA = 0.25
DELTA = 2.0
DEVICE = 'cuda:1' if torch.cuda.is_available() else 'cpu'

# 实验 Prompt 数据集 (涵盖高熵与低熵场景)
PROMPTS = [
    {"text": "The environmental impact of fashion industry is", "type": "high-entropy"},
    {"text": "Photosynthesis is a process used by plants and other organisms to", "type": "low-entropy"},
    {"text": "In a surprise move, the government decided to", "type": "high-entropy"},
    {"text": "The Pythagorean theorem states that in a right-angled triangle,", "type": "low-entropy"},
    {"text": "The future of space exploration will likely involve", "type": "high-entropy"},
    {"text": "Newton's first law of motion states that an object at rest", "type": "low-entropy"},
    {"text": "The psychological effects of social media on teenagers are", "type": "high-entropy"},
    {"text": "The chemical formula for water is H2O, which means", "type": "low-entropy"},
    {"text": "Exploring the depths of the ocean reveals a world of", "type": "high-entropy"},
    {"text": "The capital city of France is Paris, which is known for", "type": "low-entropy"}
]

def run_pipeline():
    """执行三阶段实验管线。"""
    results = []
    
    # --- 阶段 1: 文本生成 (Generation) ---
    # 采用顺序加载模式以节省显存 (Sequential Load-Process-Unload)
    generator = WatermarkGenerator(GEN_MODEL, device=DEVICE, gamma=GAMMA, delta=DELTA)
    tokenizer = generator.tokenizer # 保存分词器引用用于后续 Z-score 检测
    
    print("\n>>> Phase 1: Generation Phase Starting...")
    for item in PROMPTS:
        print(f"Processing: {item['text'][:40]}...")
        baseline = generator.generate(item['text'], with_watermark=False)
        watermarked = generator.generate(item['text'], with_watermark=True)
        
        results.append({
            "prompt": item['text'],
            "type": item['type'],
            "baseline_text": baseline,
            "watermarked_text": watermarked
        })
    
    generator.unload()
    del generator

    # --- 阶段 2: 鲁棒性攻击 (Attack) ---
    attacker = WatermarkAttacker(ATTACK_MODEL, device=DEVICE)
    
    print("\n>>> Phase 2: Attack Phase (T5 Paraphrase) Starting...")
    for res in results:
        print(f"Attacking text: {res['prompt'][:40]}...")
        res['paraphrased_text'] = attacker.paraphrase(res['watermarked_text'])
    
    attacker.unload()
    del attacker

    # --- 阶段 3: 量化评估 (Evaluation) ---
    evaluator = WatermarkEvaluator(device=DEVICE, gamma=GAMMA, judge_model_path=JUDGE_MODEL)
    
    print("\n>>> Phase 3: Evaluation Phase (Z-score & PPL) Starting...")
    for res in results:
        print(f"Evaluating metrics: {res['prompt'][:40]}...")
        # 计算 Z-score (统计显著性)
        res['z_baseline'] = evaluator.compute_z_score(res['baseline_text'], tokenizer)['z_score']
        res['z_watermarked'] = evaluator.compute_z_score(res['watermarked_text'], tokenizer)['z_score']
        res['z_paraphrased'] = evaluator.compute_z_score(res['paraphrased_text'], tokenizer)['z_score']
        
        # 计算 PPL (自然度/流畅度)
        res['ppl_baseline'] = evaluator.compute_ppl(res['baseline_text'])
        res['ppl_watermarked'] = evaluator.compute_ppl(res['watermarked_text'])
    
    evaluator.unload()

    # --- 结果持久化 ---
    output_file = 'experiment_results.jsonl'
    with open(output_file, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(json.dumps(res) + '\n')
            
    print(f"\n[Success] Pipeline finished! Results saved to: {output_file}")
    
    # 打印简要汇总报表
    print("\n" + "="*80)
    print(f"{'Prompt (Prefix)':<40} | {'Z-Base':>7} | {'Z-Wat':>7} | {'Z-Atk':>7} | {'PPL-Wat':>7}")
    print("-"*80)
    for res in results:
        print(f"{res['prompt'][:37]+'...':<40} | {res['z_baseline']:7.2f} | {res['z_watermarked']:7.2f} | {res['z_paraphrased']:7.2f} | {res['ppl_watermarked']:7.2f}")
    print("="*80)

if __name__ == "__main__":
    run_pipeline()
