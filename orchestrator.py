import os
import json
import torch
from core_classes import WatermarkGenerator, WatermarkAttacker, WatermarkEvaluator
from transformers import AutoTokenizer

# Config Paths
MODEL_DIR = '/data1/cyt/models/'
GEN_MODEL = os.path.join(MODEL_DIR, 'facebook--opt-1.3b')
ATTACK_MODEL = os.path.join(MODEL_DIR, 'Vamsi--T5_Paraphrase_Paws')
JUDGE_MODEL = os.path.join(MODEL_DIR, 'gpt2-large')

# Params
GAMMA = 0.25
DELTA = 2.0
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Prompts
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
    results = []
    
    # --- PHASE 1: GENERATION ---
    generator = WatermarkGenerator(GEN_MODEL, device=DEVICE, gamma=GAMMA, delta=DELTA)
    tokenizer = generator.tokenizer # Keep a ref to tokenizer for z-score later
    
    print("\n--- Starting Generation Phase ---")
    for item in PROMPTS:
        print(f"Generating for: {item['text'][:30]}...")
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

    # --- PHASE 2: ATTACK ---
    attacker = WatermarkAttacker(ATTACK_MODEL, device=DEVICE)
    
    print("\n--- Starting Attack Phase ---")
    for res in results:
        print(f"Attacking text for: {res['prompt'][:30]}...")
        res['paraphrased_text'] = attacker.paraphrase(res['watermarked_text'])
    
    attacker.unload()
    del attacker

    # --- PHASE 3: EVALUATION ---
    evaluator = WatermarkEvaluator(device=DEVICE, gamma=GAMMA, judge_model_path=JUDGE_MODEL)
    
    print("\n--- Starting Evaluation Phase ---")
    for res in results:
        print(f"Evaluating: {res['prompt'][:30]}...")
        # Z-scores
        res['z_baseline'] = evaluator.compute_z_score(res['baseline_text'], tokenizer)['z_score']
        res['z_watermarked'] = evaluator.compute_z_score(res['watermarked_text'], tokenizer)['z_score']
        res['z_paraphrased'] = evaluator.compute_z_score(res['paraphrased_text'], tokenizer)['z_score']
        
        # PPL
        res['ppl_baseline'] = evaluator.compute_ppl(res['baseline_text'])
        res['ppl_watermarked'] = evaluator.compute_ppl(res['watermarked_text'])
    
    evaluator.unload()

    # --- SAVE RESULTS ---
    output_file = 'experiment_results.jsonl'
    with open(output_file, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(json.dumps(res) + '\n')
            
    print(f"\nPipeline finished! Results saved to {output_file}")
    
    # Quick Summary
    for res in results:
        print(f"\nPrompt: {res['prompt'][:40]} ({res['type']})")
        print(f"  Z-score (Base/W/Para): {res['z_baseline']:.2f} / {res['z_watermarked']:.2f} / {res['z_paraphrased']:.2f}")
        print(f"  PPL (Base/W):           {res['ppl_baseline']:.2f} / {res['ppl_watermarked']:.2f}")

if __name__ == "__main__":
    run_pipeline()
