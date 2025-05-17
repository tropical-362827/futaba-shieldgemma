from transformers import AutoProcessor, ShieldGemma2ForImageClassification
from PIL import Image
import requests
import torch
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="ShieldGemma画像分類テスト")
    
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="分類する画像のURL"
    )
    
    return parser.parse_args()

args = parse_args()
model_id = "google/shieldgemma-2-4b-it"

print(f"画像URL: {args.url}")
image = Image.open(requests.get(args.url, stream=True).raw)

model = ShieldGemma2ForImageClassification.from_pretrained(model_id).eval()
processor = AutoProcessor.from_pretrained(model_id)

image = image.convert("RGB")
model_inputs = processor(images=[image], return_tensors="pt")

with torch.inference_mode():
    scores = model(**model_inputs)

print(scores.probabilities)

# ラベル固定
categories = [
    "Dangerous Content",
    "Sexually Explicit",
    "Violence & Gore"
]

yes_no_labels = ["Yes", "No"]

# 出力を整形して表示
def display_shieldgemma_output(probabilities_tensor):
    for i, probs in enumerate(probabilities_tensor):
        print(f"{categories[i]}:")
        for j in range(2):
            label = yes_no_labels[j]
            score = probs[j].item() * 100
            print(f"  {label}: {score:.2f}%")
        print()  # 空行で区切る

display_shieldgemma_output(scores.probabilities)