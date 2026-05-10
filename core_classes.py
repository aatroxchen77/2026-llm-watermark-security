import torch
import json
import numpy as np
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer
from watermark_processor import WatermarkLogitsProcessor, WatermarkDetector

class WatermarkGenerator:
    def __init__(self, model_path, device='cuda', gamma=0.25, delta=2.0):
        self.device = device
        self.model_path = model_path
        print(f"Loading generator model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path).to(device)
        self.gamma = gamma
        self.delta = delta
        self.watermark_processor = WatermarkLogitsProcessor(
            vocab=list(self.tokenizer.get_vocab().values()),
            gamma=gamma,
            delta=delta
        )

    def generate(self, prompt, max_new_tokens=200, min_new_tokens=200, with_watermark=True):
        inputs = self.tokenizer(prompt, return_tensors='pt').to(self.device)
        
        logits_processor = [self.watermark_processor] if with_watermark else []
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            min_new_tokens=min_new_tokens,
            do_sample=True,
            top_k=50,
            logits_processor=logits_processor
        )
        
        return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

    def unload(self):
        del self.model
        torch.cuda.empty_cache()

class WatermarkAttacker:
    def __init__(self, model_path, device='cuda'):
        self.device = device
        print(f"Loading attacker model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(device)

    def paraphrase(self, text):
        # T5-style paraphrase prompt
        input_text = "paraphrase: " + text + " </s>"
        inputs = self.tokenizer.encode_plus(input_text, pad_to_max_length=True, return_tensors="pt")
        
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)

        outputs = self.model.generate(
            input_ids=input_ids, 
            attention_mask=attention_mask,
            max_length=512,
            do_sample=True,
            top_k=120,
            top_p=0.95,
            early_stopping=True
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)

    def unload(self):
        del self.model
        torch.cuda.empty_cache()

class WatermarkEvaluator:
    def __init__(self, device='cuda', gamma=0.25, judge_model_path=None):
        self.device = device
        self.gamma = gamma
        self.judge_model_path = judge_model_path
        self.judge_model = None
        self.judge_tokenizer = None

    def load_judge(self):
        if self.judge_model_path:
            print(f"Loading judge model from {self.judge_model_path}...")
            self.judge_tokenizer = AutoTokenizer.from_pretrained(self.judge_model_path)
            self.judge_model = AutoModelForCausalLM.from_pretrained(self.judge_model_path).to(self.device)

    def compute_z_score(self, text, tokenizer):
        # We need an instance of detector for every check because it might use different vocab/gamma
        detector = WatermarkDetector(
            vocab=list(tokenizer.get_vocab().values()),
            gamma=self.gamma,
            seeding_scheme='simple_1',
            device=self.device,
            tokenizer=tokenizer
        )
        return detector.detect(text)

    def compute_ppl(self, text):
        if not self.judge_model:
            self.load_judge()
            
        inputs = self.judge_tokenizer(text, return_tensors='pt').to(self.device)
        input_ids = inputs['input_ids']
        
        with torch.no_grad():
            outputs = self.judge_model(input_ids, labels=input_ids)
            loss = outputs.loss
            
        return torch.exp(loss).item()

    def unload(self):
        if self.judge_model:
            del self.judge_model
            torch.cuda.empty_cache()
