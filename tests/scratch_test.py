import os
import sys
import torch
import pandas as pd
from PIL import Image

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.inference import PlaylifyModel

model = PlaylifyModel(os.path.join(ROOT_DIR, 'models'))
tsv_path = os.path.join(ROOT_DIR, 'research', 'data', 'cleaned_album_dataset.tsv')
df = pd.read_csv(tsv_path, sep='\t')
latin_df = df[df['genre'] == 'Latin']

preds = []
for idx in latin_df['album_index']:
    img_path = os.path.join(ROOT_DIR, 'data', 'images', f'{idx}.jpg')
    if not os.path.exists(img_path):
        continue
    img = Image.open(img_path).convert('RGB')
    tensor = model.transform(img).unsqueeze(0).to(model.device)
    with torch.no_grad():
        features = model.pool(model.feature_extractor(tensor))
        logits = model.classifier_head(torch.flatten(features, 1))
        probs = torch.nn.functional.softmax(logits, dim=1)[0]
        p, class_idx = torch.max(probs, 0)
        pred = model.le.inverse_transform([class_idx.item()])[0]
        preds.append(pred)

print("Predictions for Latin albums:")
print(pd.Series(preds).value_counts())
