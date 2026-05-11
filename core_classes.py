import torch
import json
import numpy as np
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer
from watermark_processor import WatermarkLogitsProcessor, WatermarkDetector

class WatermarkGenerator:
    """
    水印文本生成器类。
    负责加载自回归语言模型（如 OPT），并集成 Logit 偏置处理器以在生成过程中植入水印。
    """
    def __init__(self, model_path, device='cuda', gamma=0.25, delta=2.0):
        """
        初始化生成器。
        
        Args:
            model_path (str): 本地模型路径或 HuggingFace 模型 ID。
            device (str): 运行设备 (e.g., 'cuda:0', 'cpu')。
            gamma (float): 绿名单比例。
            delta (float): 水印偏置强度。
        """
        self.device = device
        self.model_path = model_path
        print(f"Loading generator model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path).to(device)
        self.gamma = gamma
        self.delta = delta
        # 初始化水印 Logit 处理器
        self.watermark_processor = WatermarkLogitsProcessor(
            vocab=list(self.tokenizer.get_vocab().values()),
            gamma=gamma,
            delta=delta
        )

    def generate(self, prompt, max_new_tokens=200, min_new_tokens=200, with_watermark=True):
        """
        生成文本。
        
        Args:
            prompt (str): 输入提示词。
            max_new_tokens (int): 最大生成长度。
            min_new_tokens (int): 最小生成长度（确保统计量充足）。
            with_watermark (bool): 是否开启水印植入。
            
        Returns:
            str: 解码后的生成文本。
        """
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
        """释放显存空间。"""
        del self.model
        torch.cuda.empty_cache()

class WatermarkAttacker:
    """
    水印攻击器类（鲁棒性测试）。
    利用 Seq2Seq 模型（如 T5）对带水印文本进行释义攻击（Paraphrasing）。
    """
    def __init__(self, model_path, device='cuda'):
        """
        初始化攻击器。
        
        Args:
            model_path (str): T5 等释义模型的路径。
            device (str): 运行设备。
        """
        self.device = device
        print(f"Loading attacker model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(device)

    def paraphrase(self, text):
        """
        对输入文本进行语义改写。
        
        Args:
            text (str): 原始文本。
            
        Returns:
            str: 改写后的文本。
        """
        # 构造 T5 释义提示词
        input_text = "paraphrase: " + text + " </s>"
        inputs = self.tokenizer(input_text, padding=True, truncation=True, return_tensors="pt")
        
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
        """释放显存空间。"""
        del self.model
        torch.cuda.empty_cache()

class WatermarkEvaluator:
    """
    水印评估器类。
    负责计算 Z-score 统计量、文本困惑度 (PPL) 等核心量化指标。
    """
    def __init__(self, device='cuda', gamma=0.25, judge_model_path=None):
        """
        初始化评估器。
        
        Args:
            device (str): 运行设备。
            gamma (float): 水印参数 gamma，需与生成端一致。
            judge_model_path (str): 用于计算 PPL 的评判模型路径（通常选用较大的通用模型）。
        """
        self.device = device
        self.gamma = gamma
        self.judge_model_path = judge_model_path
        self.judge_model = None
        self.judge_tokenizer = None

    def load_judge(self):
        """延迟加载评判模型，以优化内存管理。"""
        if self.judge_model_path:
            print(f"Loading judge model (PPL) from {self.judge_model_path}...")
            self.judge_tokenizer = AutoTokenizer.from_pretrained(self.judge_model_path)
            self.judge_model = AutoModelForCausalLM.from_pretrained(self.judge_model_path).to(self.device)

    def compute_z_score(self, text, tokenizer):
        """
        计算文本的 Z-score 统计量。
        
        Args:
            text (str): 待检测文本。
            tokenizer: 生成模型对应的分词器。
            
        Returns:
            dict: 包含 z_score, prediction 等信息的字典。
        """
        detector = WatermarkDetector(
            vocab=list(tokenizer.get_vocab().values()),
            gamma=self.gamma,
            seeding_scheme='simple_1', # 对应原始论文的基础方案
            device=self.device,
            tokenizer=tokenizer
        )
        return detector.detect(text)

    def compute_ppl(self, text):
        """
        计算文本困惑度 (Perplexity)。
        PPL 越低，文本越自然、越符合语言概率分布。
        """
        if not self.judge_model:
            self.load_judge()
            
        inputs = self.judge_tokenizer(text, return_tensors='pt').to(self.device)
        input_ids = inputs['input_ids']
        
        with torch.no_grad():
            outputs = self.judge_model(input_ids, labels=input_ids)
            loss = outputs.loss
            
        return torch.exp(loss).item()

    def unload(self):
        """释放显存空间。"""
        if self.judge_model:
            del self.judge_model
            torch.cuda.empty_cache()
