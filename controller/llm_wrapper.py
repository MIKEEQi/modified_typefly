import os
import openai
from openai import Stream, ChatCompletion

GPT3 = "gpt-3.5-turbo-16k"
GPT4 = "gpt-4"
LLAMA3 = "meta-llama/Meta-Llama-3-8B-Instruct"
DEEPSEEK = 'deepseek-chat'

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
chat_log_path = os.path.join(CURRENT_DIR, "assets/chat_log.txt")

class LLMWrapper:
    def __init__(self, temperature=0.0):
        self.temperature = temperature
        self.llama_client = openai.OpenAI(
            # base_url="http://10.66.41.78:8000/v1",
            base_url="http://localhost:8000/v1",
            api_key="token-abc123",
        )

        self.gpt_client = openai.OpenAI(
            api_key="api")

        self.deepseek_client = openai.OpenAI(
            base_url='https://api.deepseek.com',
            api_key='sk-2d9d0f32e6bf4965a0bf998b1e5d5985'
        )

    def request(self, prompt, model_name=DEEPSEEK, stream=False, task='typefly') -> str | Stream[ChatCompletion.ChatCompletionChunk]:
        if model_name == LLAMA3:
            client = self.llama_client
        elif model_name == GPT4 or model_name==GPT3:
            client = self.gpt_client
        else:
            client = self.deepseek_client

        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            stream=stream,
        )

        if task == 'typefly':
            # save the message in a txt
            with open(chat_log_path, "a") as f:
                f.write(prompt + "\n---\n")
                if not stream:
                    f.write(response.model_dump_json(indent=2) + "\n---\n")

        elif task == 'rewrite':
            with open(os.path.join(CURRENT_DIR, 'assets/attack/harm_instructs.txt'), 'a') as f:
                f.write(response.choices[0].message.content + "\n---\n")

        elif task == 'attack':
            with open(os.path.join(CURRENT_DIR, 'assets/attack/attack_results.txt'), 'a') as f:
                f.write(response.choices[0].message.content + "\n---\n")

        elif task == 'explain':
            with open(os.path.join(CURRENT_DIR, 'assets/attack/attack_explain.txt'), 'a') as f:
                f.write(response.choices[0].message.content + "\n---\n")

        if stream:
            return response


        return response.choices[0].message.content