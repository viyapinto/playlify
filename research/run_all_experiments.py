import os
import time
import json
import joblib
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import models, transforms
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_class_weight
from PIL import Image
from tqdm import tqdm

LABELS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'cleaned_album_dataset.tsv')
IMAGE_DIR = 'data/images'
RESULTS_DIR = 'research/results'
EPOCHS = 1  # 1 epoch for rapid experimentation to get directional signal
BATCH_SIZE = 64
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

os.makedirs(RESULTS_DIR, exist_ok=True)

class AlbumDataset(Dataset):
    def __init__(self, df, transform=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform
        
    def __len__(self):
        return len(self.df)
        
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        album_index = row['album_index']
        img_path = os.path.join(IMAGE_DIR, f"{album_index}.jpg")
        try:
            image = Image.open(img_path).convert('RGB')
        except:
            image = Image.new('RGB', (224, 224))
        if self.transform:
            image = self.transform(image)
        return image, row['encoded_genre']

# Data Prep
print("Loading data...")
df = pd.read_csv(LABELS_FILE, sep='\t')
valid_indices = [idx for idx in df['album_index'] if os.path.exists(os.path.join(IMAGE_DIR, f"{idx}.jpg"))]
df = df[df['album_index'].isin(valid_indices)]
le = LabelEncoder()
df['encoded_genre'] = le.fit_transform(df['genre'])
num_classes = len(le.classes_)

train_df = df[df['set'] == 'train'].sample(frac=0.05, random_state=42)
val_df = df[df['set'] == 'val'].sample(frac=0.05, random_state=42)
test_df = df[df['set'] == 'test'].sample(frac=0.05, random_state=42)

# Base Transforms
base_train_tf = transforms.Compose([
    transforms.Resize(256), transforms.RandomCrop(224), transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.1),
    transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
val_test_tf = transforms.Compose([
    transforms.Resize(256), transforms.CenterCrop(224),
    transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_dataset = AlbumDataset(val_df, transform=val_test_tf)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

def create_model():
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    return model.to(device)

def train_and_eval(name, train_loader, criterion, optimizer, model):
    print(f"\n--- Running Experiment: {name} ---")
    model.train()
    for _ in range(EPOCHS):
        for images, labels in tqdm(train_loader, desc=f"Train"):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in tqdm(val_loader, desc="Eval"):
            images = images.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())
            
    report = classification_report(all_labels, all_preds, output_dict=True, zero_division=0)
    results = {
        'accuracy': report['accuracy'],
        'macro_f1': report['macro avg']['f1-score'],
        'weighted_f1': report['weighted avg']['f1-score']
    }
    with open(f'{RESULTS_DIR}/{name}.json', 'w') as f:
        json.dump(results, f, indent=4)
    print(f"Results for {name}: Acc: {results['accuracy']:.4f}, Macro F1: {results['macro_f1']:.4f}")
    return results

# 1. Baseline Repro
train_dataset = AlbumDataset(train_df, transform=base_train_tf)
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
model = create_model()
train_and_eval("baseline_1ep", train_loader, nn.CrossEntropyLoss(), optim.Adam(model.parameters(), lr=1e-4), model)

# 2. Exp 1: Augmentation
aug_tf = transforms.Compose([
    transforms.Resize(256), transforms.RandomCrop(224), transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15), transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
    transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
aug_train_loader = DataLoader(AlbumDataset(train_df, transform=aug_tf), batch_size=BATCH_SIZE, shuffle=True)
model = create_model()
train_and_eval("exp1_augmentation", aug_train_loader, nn.CrossEntropyLoss(), optim.Adam(model.parameters(), lr=1e-4), model)

# 3. Exp 2: Class Imbalance
class_weights = compute_class_weight('balanced', classes=np.unique(train_df['encoded_genre']), y=train_df['encoded_genre'])
class_weights = torch.tensor(class_weights, dtype=torch.float32).to(device)
model = create_model()
train_and_eval("exp2_class_weights", train_loader, nn.CrossEntropyLoss(weight=class_weights), optim.Adam(model.parameters(), lr=1e-4), model)

# 4. Exp 3: Staged Fine-tuning (freeze backbone)
model = create_model()
for param in model.features.parameters():
    param.requires_grad = False
train_and_eval("exp3_staged_frozen", train_loader, nn.CrossEntropyLoss(), optim.Adam(model.classifier.parameters(), lr=1e-3), model)

# 5. Exp 4: Hyperparameters (Larger batch, smaller LR)
train_loader_bs128 = DataLoader(train_dataset, batch_size=128, shuffle=True)
model = create_model()
train_and_eval("exp4_hyperparams", train_loader_bs128, nn.CrossEntropyLoss(), optim.Adam(model.parameters(), lr=5e-5), model)

print("\n--- ALL EXPERIMENTS COMPLETED ---")
