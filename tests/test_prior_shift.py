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

# Compute class priors
class_counts = df['genre'].value_counts()
class_priors = class_counts / class_counts.sum()

# Map priors to tensor in the order of label encoder
priors_tensor = torch.zeros(len(model.le.classes_), device=model.device)
for i, c in enumerate(model.le.classes_):
    priors_tensor[i] = class_priors[c]

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
        
        # Apply prior shift
        adjusted_probs = probs / priors_tensor
        adjusted_probs = adjusted_probs / adjusted_probs.sum()
        
        p, class_idx = torch.max(adjusted_probs, 0)
        pred = model.le.inverse_transform([class_idx.item()])[0]
        preds.append(pred)

print("Predictions for Latin albums with Prior Shift:")
print(pd.Series(preds).value_counts())
