import torch
import pandas as pd
from PIL import Image
from backend.inference import PlaylifyModel
import os

model = PlaylifyModel('models')
df = pd.read_csv('cleaned_album_dataset.tsv', sep='\t')

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
    img_path = f'data/images/{idx}.jpg'
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
