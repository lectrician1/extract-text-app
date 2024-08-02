import os
import gradio as gr
import re
import torch
import numpy as np


from PIL import Image
from transformers import DonutProcessor, VisionEncoderDecoderModel

title = "OCR using Donut"
description = """
This demo application uses `naver-clova-ix/donut-base` model to extract text from images.
"""
article = "Check out [naver-clova-ix/donut-base](https://huggingface.co/naver-clova-ix/donut-base) documentation that this demo is based off of."

checkpoint = "naver-clova-ix/donut-base"

processor = DonutProcessor.from_pretrained(checkpoint)
model = VisionEncoderDecoderModel.from_pretrained(checkpoint)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# prepare decoder inputs
task_prompt = "<s_synthdog>"
decoder_input_ids = processor.tokenizer(
    task_prompt, add_special_tokens=False, return_tensors="pt"
).input_ids



device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

def predict(image):
    pixel_values = processor(image, return_tensors="pt").pixel_values

    outputs = model.generate(
        pixel_values.to(device),
        decoder_input_ids=decoder_input_ids.to(device),
        max_length=model.decoder.config.max_position_embeddings,
        early_stopping=True,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id,
        use_cache=True,
        num_beams=1,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
        return_dict_in_generate=True,
    )

    sequence = processor.batch_decode(outputs.sequences)[0]
    sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(
        processor.tokenizer.pad_token, ""
    )
    sequence = re.sub(
        r"<.*?>", "", sequence, count=1
    ).strip()  # remove first task start token
    return processor.token2json(sequence)["text_sequence"]

# load image from the IAM database
path = "C:\\Users\\sedeegan\\cropped_page_0.png"
image = Image.open(path).convert("RGB")

print(predict(image))