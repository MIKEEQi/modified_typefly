from llm_wrapper import LLMWrapper, LLAMA3, GPT4

model = LLMWrapper()

with open('./assets/attack/harm_instructions.txt', 'r') as f:
    original_instructs = f.read().split('\n\n')

print(original_instructs)
with open('./assets/attack/instruction_rewrite.txt', 'r') as f:
    prompt = f.read()

for instruct in original_instructs:
    prompt_ins = prompt + instruct
    new_ins = model.request(prompt=prompt_ins, task='prompt rewrite', model_name=GPT4)
    print(new_ins)
