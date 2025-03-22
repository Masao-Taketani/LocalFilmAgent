import json
import random
from dataclasses import dataclass
from typing import Optional
from tqdm import tqdm
import os
import soundfile

from utils import read_json, toString, contains_digit, prompt_format, InferCodeParams
import ChatTTS


MALE_PATH = "spk/male"
FEMALE_PATH = "spk/female"
MODEL_PATH = "model"
OUTDIR_PATH = "../FilmAgent/Audio"
os.makedirs(OUTDIR_PATH, exist_ok=True)
ACTOS_PATH = "../FilmAgent/Script/actors_profile.json"
SCRIPT_PATH = "../FilmAgent/Script/script/0.json"
AUDIO_PATH = "../FilmAgent/audio_files"
PARAMS_INFER_CODE = {'prompt':'[speed_3]', 'temperature':0.3,'top_P':0.9, 'top_K':1}


def create_spk(male_path, female_path):
    spk = {"male": [], "female": []}
    for file in os.listdir(male_path):
        t = torch.load(os.path.join(male_path, file))
        spk['male'].append(t)
    for file in os.listdir(female_path):
        t = torch.load(os.path.join(female_path, file))
        spk['female'].append(t)
    return spk

def create_name2chatspeaker_dict(actos_path):
    chat_speaker_female = [0, 1, 2, 3, 4]
    chat_speaker_male = [0, 1, 2, 3, 4]
    random.shuffle(chat_speaker_female) 
    random.shuffle(chat_speaker_male) 
    # ChatTTS: Assign a voice to each character
    name2chatspeaker = {}
    roles = read_json(actos_path)
    for role in roles:
        name2chatspeaker[role['name']] = {}
        if role['gender'].lower() == "male":
            name2chatspeaker[role['name']]['id'] = chat_speaker_male[0]
            name2chatspeaker[role['name']]['gender'] = "male"
            chat_speaker_male.pop(0)
        else:
            name2chatspeaker[role['name']]['id'] = chat_speaker_female[0]
            name2chatspeaker[role['name']]['gender'] = "female"
            chat_speaker_female.pop(0)
    return name2chatspeaker

def create_scripts():
    invalid_characters_map = {
        "!": ".",
        "?": ".",
        "'": ",",
        ':': ',',
        ';': ',',
        '!': '.',
        '(': ',',
        ')': ',',
        '[': ',',
        ']': ',',
        '>': ',',
        '<': ',',
        '-': ','
    }

    script = read_json(SCRIPT_PATH)
    lines = []
    for scene in script:
        for event in scene['scene']:
            if "content" in event.keys():
                l = event["content"]
                lines.append({"speaker": event["speaker"], "content": prompt_format(l, invalid_characters_map)+"[uv_break]"})
    return line

def create_audio_files(chat, lines, name2chatspeaker, spk):
    for i, line in enumerate(tqdm(lines)):
        params = {"gender": name2chatspeaker[line['speaker']]['gender'], 
                  "text": line['content'], 
                  "id": name2chatspeaker[line['speaker']]['id'], 
                  "params_infer_code": PARAMS_INFER_CODE}
        speaker = spk[params['gender']][params['id']]
        params_infer_code = params['params_infer_code']
        params_infer_code['spk_emb'] = speaker
        params_infer_code = InferCodeParams(**params_infer_code)
        
        print("text: ", params['text'])
        
        wavs = chat.infer(params['text'],
                        #   do_text_normalization=True,
                        skip_refine_text=True,
                        params_infer_code=params_infer_code)
        soundfile.write(os.path.join(OUTDIR_PATH, f"{i}.wav"), wavs[0], 24000)


if __name__ == "__main__":
    chat = ChatTTS.Chat()
    chat.load(source='local', custom_path=MODEL_PATH, compile=False)
