import os
import json
import joblib
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from sklearn.metrics import classification_report, confusion_matrix
from PIL import Image
from tqdm import tqdm

LABELS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'cleaned_album_dataset.tsv')
IMAGE_DIR = 'data/images'
MODELS_DIR = 'models'
BATCH_SIZE = 64

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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
        except Exception:
            image = Image.new('RGB', (224, 224))
            
        if self.transform:
            image = self.transform(image)
            
        label = row['encoded_genre']
        return image, label, album_index

def evaluate_model(model_path='models/finetuned_model.pth', report_name='baseline_results.json'):
    print(f"Evaluating {model_path} on {device}")
    
    # Load dataset
    df = pd.read_csv(LABELS_FILE, sep='\t')
    le = joblib.load(os.path.join(MODELS_DIR, 'le.pkl'))
    num_classes = len(le.classes_)
    
    # Ensure encoded_genre matches LE
    df['encoded_genre'] = le.transform(df['genre'])
    
    test_df = df[df['set'] == 'test']
    
    val_test_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    test_dataset = AlbumDataset(test_df, transform=val_test_transform)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
    # Load model
    model = models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model = model.to(device)
    model.eval()
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels, _ in tqdm(test_loader, desc="Testing"):
            images = images.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())
            
    # Metrics
    report = classification_report(all_labels, all_preds, labels=range(num_classes), target_names=le.classes_, output_dict=True)
    
    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds, labels=range(num_classes))
    
    results = {
        'accuracy': report['accuracy'],
        'macro_f1': report['macro avg']['f1-score'],
        'weighted_f1': report['weighted avg']['f1-score'],
        'per_class_f1': {genre: report[genre]['f1-score'] for genre in le.classes_},
        'confusion_matrix': cm.tolist()
    }
    
    print("\n--- RESULTS ---")
    print(f"Accuracy:    {results['accuracy']*100:.2f}%")
    print(f"Macro F1:    {results['macro_f1']:.4f}")
    print(f"Weighted F1: {results['weighted_f1']:.4f}")
    
    # Save results
    os.makedirs('research/results', exist_ok=True)
    out_path = f'research/results/{report_name}'
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"Results saved to {out_path}")

if __name__ == '__main__':
    evaluate_model()
