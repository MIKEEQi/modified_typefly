import os
import torch
from PIL import Image
from transformers import LlavaProcessor, LlavaForConditionalGeneration

LLAVA = 'llava-hf/llava-1.5-7b-hf'

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
chat_log_path = os.path.join(CURRENT_DIR, "assets/chat_log.txt")

class LlavaWrapper:
    def __init__(self, temperature=0.2):
        self.temperature = temperature
        self.processor = LlavaProcessor.from_pretrained(LLAVA)
        self.model = LlavaForConditionalGeneration.from_pretrained(LLAVA).to("cuda" if torch.cuda.is_available() else "cpu")
        self.device = self.model.device

    def request(self, prompt, image_path=None, task='typefly', max_tokens=256, stream=False):
        image = Image.open(image_path).convert("RGB") if image_path else None
        messages = [{"role": "user", "content": prompt}]

        inputs = self.processor(
            messages,
            images=image,
            return_tensors="pt"
        ).to(self.device)

        output = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=self.temperature
        )

        decoded = self.processor.batch_decode(output, skip_special_tokens=True)[0]

        # --- Task-based logging ---
        if task == 'typefly':
            with open(chat_log_path, "a") as f:
                f.write(prompt + "\n---\n")
                f.write(decoded + "\n---\n")
        elif task == 'rewrite':
            with open(os.path.join(CURRENT_DIR, 'assets/attack/harm_instructs.txt'), 'a') as f:
                f.write(decoded + "\n---\n")
        elif task == 'attack':
            with open(os.path.join(CURRENT_DIR, 'assets/attack/attack_results.txt'), 'a') as f:
                f.write(decoded + "\n---\n")
        elif task == 'explain':
            with open(os.path.join(CURRENT_DIR, 'assets/attack/attack_explain.txt'), 'a') as f:
                f.write(decoded + "\n---\n")

        return decoded
