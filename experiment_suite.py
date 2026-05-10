import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from watermark_processor import WatermarkLogitsProcessor, WatermarkDetector
import random
import numpy as np

# Config
MODEL_PATH = '/data1/cyt/models/facebook--opt-1.3b'
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
GEN_LEN = 200
NUM_SAMPLES = 5 # Small number for quick verification
GAMMA = 0.25
DELTA = 2.0

def load_model():
    print(f"Loading model from {MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(MODEL_PATH).to(DEVICE)
    return model, tokenizer

def random_substitution_attack(text, p=0.1):
    """Simulate a simple attack by randomly deleting words."""
    words = text.split()
    if not words: return text
    new_words = [w for w in words if random.random() > p]
    return " ".join(new_words)

def run_experiment():
    model, tokenizer = load_model()
    
    watermark_processor = WatermarkLogitsProcessor(vocab=list(tokenizer.get_vocab().values()),
                                                    gamma=GAMMA,
                                                    delta=DELTA)
    
    detector = WatermarkDetector(vocab=list(tokenizer.get_vocab().values()),
                                 gamma=GAMMA,
                                 seeding_scheme='simple_1',
                                 device=DEVICE,
                                 tokenizer=tokenizer)

    prompts = [
        "The development of artificial intelligence has led to",
        "In the future, humans will likely live on Mars because",
        "The key to a successful career in software engineering is",
        "Global warming is one of the most pressing issues",
        "The history of cryptography dates back to ancient"
    ]

    results = []

    for i, prompt in enumerate(prompts[:NUM_SAMPLES]):
        print(f"\nSample {i+1}/{NUM_SAMPLES}...")
        inputs = tokenizer(prompt, return_tensors='pt').to(DEVICE)

        # 1. No Watermark
        out_no = model.generate(**inputs, max_new_tokens=GEN_LEN, do_sample=True, top_k=50)
        text_no = tokenizer.batch_decode(out_no, skip_special_tokens=True)[0]
        score_no = detector.detect(text_no)

        # 2. With Watermark
        out_w = model.generate(**inputs, max_new_tokens=GEN_LEN, do_sample=True, top_k=50, 
                               logits_processor=[watermark_processor])
        text_w = tokenizer.batch_decode(out_w, skip_special_tokens=True)[0]
        score_w = detector.detect(text_w)

        # 3. Attack on Watermarked Text
        text_attacked = random_substitution_attack(text_w, p=0.2) # 20% words removed
        score_attacked = detector.detect(text_attacked)

        results.append({
            'no_w': score_no['z_score'],
            'with_w': score_w['z_score'],
            'attacked': score_attacked['z_score']
        })
        
        print(f"  Z-score (No W):   {score_no['z_score']:.4f}")
        print(f"  Z-score (With W): {score_w['z_score']:.4f}")
        print(f"  Z-score (Attack): {score_attacked['z_score']:.4f}")

    # Summary
    no_w_avg = np.mean([r['no_w'] for r in results])
    with_w_avg = np.mean([r['with_w'] for r in results])
    attack_avg = np.mean([r['attacked'] for r in results])

    print("\n" + "="*50)
    print("EXPERIMENT SUMMARY")
    print("="*50)
    print(f"Average Z-score (No Watermark):   {no_w_avg:.4f}")
    print(f"Average Z-score (With Watermark): {with_w_avg:.4f}")
    print(f"Average Z-score (After Attack):   {attack_avg:.4f}")
    print("="*50)

if __name__ == "__main__":
    run_experiment()
