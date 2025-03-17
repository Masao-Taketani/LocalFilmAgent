import json
import subprocess
from transformers import set_seed
from transformers.pipelines.text_generation import TextGenerationPipeline

REASONING_MODEL_KEYWORDS = ["deepseek-r1", "qwq"]


def init_hf_pipe(model):
    from transformers import pipeline
    import torch
    torch_dtype = torch.float16 if "awq" in model.lower() else torch.bfloat16
    pipe = pipeline("text-generation", 
                    model=model, 
                    model_kwargs={"torch_dtype": torch_dtype}, 
                    device_map="auto")
    return pipe

def process_think_model_output(answer, show_thought):
    thought, answer = answer.split("</think>")
    answer = answer[2:]
    if show_thought:
        print("\n\n[Showing thought process STARTs here]")
        print(thought.split("<think>")[1][1:]) if thought.startswith("<think>") else print(thought)
        print("[Showing thought process ENDs here]\n\n")
    return answer

def LLMCall(prompt, platform, model_or_pipe, show_thought, num_ctx=None, max_length=None, temp=1.0):
    if platform == "ollama":
        if num_ctx is None: num_ctx = 32768 if "qwen2.5" in model_or_pipe.lower() else 131072
        prompt_dic = {"role": "user", "content": f"""{prompt}"""}
        prompt_json = json.dumps(prompt_dic)
        messages = f"""[{prompt_json}]"""
        args = rf"""{{"model": "{model_or_pipe}", "messages": {messages}, "options": {{"num_ctx": {num_ctx}, "temperature": {temp}}}, "stream": false}}"""
        with open("tmp_args.txt","w") as f:
            f.write(args)
        command = ["curl", "http://localhost:11434/api/chat", "-d", "@tmp_args.txt"]
        rlt = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        answer = json.loads(rlt.stdout)["message"]["content"]
    elif platform == "huggingface":
        prompt = model_or_pipe.tokenizer.apply_chat_template(
            [
                {"role": "user", "content": prompt},
            ], 
            tokenize=False, 
            add_generation_prompt=True
        )
        set_seed(0)
        do_sample = True if temp != 0 else False
        if max_length is None:
            max_length = 32768 if "qwen2.5" in model_or_pipe.tokenizer.name_or_path.lower() else 131072
        response = model_or_pipe(prompt,
                                 do_sample=do_sample,
                                 temperature=temp,
                                 max_length=max_length,
                                 truncation=True
        )
        answer = response[0]["generated_text"][len(prompt):]        
    else:
        raise ValueError(f"Platform {platform} is not supported.")

    if (isinstance(model_or_pipe, str) and any([keyword in model_or_pipe.lower() for keyword in REASONING_MODEL_KEYWORDS])) \
    or (isinstance(model_or_pipe, TextGenerationPipeline) and any([keyword in model_or_pipe.tokenizer.name_or_path.lower() for keyword in REASONING_MODEL_KEYWORDS])):
        answer = process_think_model_output(answer, show_thought)
    return answer

def GPTTTS(text, role):
    client = client_gpt
    response = client.audio.speech.create(
        model = "tts-1",
        voice = role,
        input = text,
        response_format = "mp3"
    )
    return response