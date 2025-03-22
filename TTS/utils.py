from dataclasses import dataclass
from typing import Optional
import json


def read_json(input_path):
    with open(input_path, 'r', encoding='utf-8',errors='ignore') as f:
        r = toString(json.load(f))
        r = r.replace("�",".")
        return json.loads(r)

def toString(input):
    return json.dumps(input, ensure_ascii=False, separators=(",", ":")) 

def contains_digit(string):
    return bool(re.search(r'\d', string))

def prompt_format(prompt, params):
    text = prompt
    for key, value in params.items():
        if isinstance(value, (dict, list)):
            value = toString(value)
        if isinstance(value, (int, float)):
            value = str(value)
        text = text.replace(key, value)
    return text


@dataclass(repr=False, eq=False)
class RefineTextParams:
    prompt: str = ""
    top_P: float = 0.7
    top_K: int = 20
    temperature: float = 0.7
    repetition_penalty: float = 1.0
    max_new_token: int = 384
    min_new_token: int = 0
    show_tqdm: bool = True
    ensure_non_empty: bool = True
    manual_seed: Optional[int] = None


@dataclass(repr=False, eq=False)
class InferCodeParams(RefineTextParams):
    prompt: str = "[speed_5]"
    spk_emb: Optional[str] = None
    spk_smp: Optional[str] = None
    txt_smp: Optional[str] = None
    temperature: float = 0.3
    repetition_penalty: float = 1.05
    max_new_token: int = 2048
    stream_batch: int = 24
    stream_speed: int = 12000
    pass_first_n_batches: int = 2