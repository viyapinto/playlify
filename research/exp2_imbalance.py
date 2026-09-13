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
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import classification_report, f1_score
from sklearn.decomposition import PCA
import torch.nn.functional as F
from sklearn.utils.class_weight import compute_class_weight
from PIL import Image
from tqdm import tqdm

# Configuration
LABELS_FILE = 'cleaned_album_dataset.tsv'
IMAGE_DIR = 'data/images'
MODELS_DIR = 'models_exp2'
EPOCHS = 5
BATCH_SIZE = 64
LEARNING_RATE = 1e-4
KNN_PCA_COMPONENTS = 128

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
            # Create dummy black image if corrupted/missing
            image = Image.new('RGB', (224, 224))
            
        if self.transform:
            image = self.transform(image)
            
        label = row['encoded_genre']
        return image, label, album_index

class FocalLoss(nn.Module):
    def __init__(self, alpha=None, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        
        if self.alpha is not None:
            alpha_t = self.alpha.gather(0, targets.data.view(-1))
            focal_loss = focal_loss * alpha_t
            
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

def main():
    print(f"Using device: {device}")
    print("Loading data...")
    df = pd.read_csv(LABELS_FILE, sep='\t')
    
    # Filter only albums that actually have an image file
    valid_indices = []
    for idx in df['album_index']:
        if os.path.exists(os.path.join(IMAGE_DIR, f"{idx}.jpg")):
            valid_indices.append(idx)
    df = df[df['album_index'].isin(valid_indices)]
    print(f"Total valid images: {len(df)}")
    
    # Encode labels
    le = LabelEncoder()
    df['encoded_genre'] = le.fit_transform(df['genre'])
    num_classes = len(le.classes_)
    
    train_df = df[df['set'] == 'train']
    val_df = df[df['set'] == 'val']
    test_df = df[df['set'] == 'test']
    
    print(f"Train size: {len(train_df)}, Val size: {len(val_df)}, Test size: {len(test_df)}")

    # Transforms
    train_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_test_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = AlbumDataset(train_df, transform=train_transform)
    val_dataset = AlbumDataset(val_df, transform=val_test_transform)
    test_dataset = AlbumDataset(test_df, transform=val_test_transform)
    full_dataset = AlbumDataset(df, transform=val_test_transform)

    # Calculate sample weights for WeightedRandomSampler
    class_counts = train_df['encoded_genre'].value_counts().sort_index().values
    class_weights_sampler = 1.0 / class_counts
    sample_weights = [class_weights_sampler[label] for label in train_df['encoded_genre']]
    sampler = WeightedRandomSampler(weights=sample_weights, num_samples=len(sample_weights), replacement=True)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    full_loader = DataLoader(full_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # Initialize Model
    print("Initializing MobileNetV2...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    # Replace final layer
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    model = model.to(device)
    
    # Compute class weights for Focal Loss
    class_weights = compute_class_weight('balanced', classes=np.unique(train_df['encoded_genre']), y=train_df['encoded_genre'])
    class_weights = torch.tensor(class_weights, dtype=torch.float32).to(device)
    
    criterion = FocalLoss(alpha=class_weights, gamma=2.0)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    best_val_f1 = -1.0
    
    print("\n--- Starting Training ---")
    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for images, labels, _ in tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Train]"):
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        train_acc = correct / total
        
        # Validation
        model.eval()
        val_preds = []
        val_labels = []
        with torch.no_grad():
            for images, labels, _ in tqdm(val_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Val]"):
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs.data, 1)
                val_preds.extend(predicted.cpu().numpy())
                val_labels.extend(labels.cpu().numpy())
                
        val_acc = (np.array(val_preds) == np.array(val_labels)).mean()
        val_macro_f1 = f1_score(val_labels, val_preds, average='macro')
        print(f"Epoch {epoch+1} - Loss: {running_loss/len(train_loader):.4f} - Train Acc: {train_acc:.4f} - Val Acc: {val_acc:.4f} - Val Macro F1: {val_macro_f1:.4f}")
        
        if val_macro_f1 > best_val_f1:
            best_val_f1 = val_macro_f1
            os.makedirs(MODELS_DIR, exist_ok=True)
            torch.save(model.state_dict(), os.path.join(MODELS_DIR, 'finetuned_model.pth'))
            print("  --> Saved new best model!")
            
    # Load Best Model for Testing
    print("\n--- Evaluating Best Model on Test Set ---")
    model.load_state_dict(torch.load(os.path.join(MODELS_DIR, 'finetuned_model.pth'), weights_only=True))
    model.eval()
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels, _ in tqdm(test_loader, desc="Testing"):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
    print(classification_report(all_labels, all_preds, labels=range(len(le.classes_)), target_names=le.classes_))
    
    # Feature Re-extraction for KNN
    print("\n--- Re-extracting Features for Similarity Search ---")
    # Remove classification head to get embeddings
    model.classifier = nn.Identity()
    model.eval()
    
    all_features = []
    
    with torch.no_grad():
        for images, _, _ in tqdm(full_loader, desc="Extracting"):
            images = images.to(device)
            features = model(images)
            all_features.append(features.cpu().numpy())
            
    all_features = np.vstack(all_features)
    
    print(f"Applying PCA (components={KNN_PCA_COMPONENTS}) to new features...")
    pca = PCA(n_components=KNN_PCA_COMPONENTS, random_state=42)
    features_pca = pca.fit_transform(all_features)
    
    print("Building NearestNeighbors index...")
    knn = NearestNeighbors(n_neighbors=10, metric='cosine', n_jobs=-1)
    knn.fit(features_pca)
    
    # Create metadata
    metadata = []
    for idx, row in df.iterrows():
        metadata.append({
            'album_index': int(row['album_index']),
            'genre': row['genre'],
            'artist_id': row['msd_artist_id'],
            'image_url': row['image_url']
        })
        
    print("Saving models and metadata to disk...")
    joblib.dump(pca, os.path.join(MODELS_DIR, 'pca.pkl'))
    joblib.dump(knn, os.path.join(MODELS_DIR, 'knn.pkl'))
    joblib.dump(le, os.path.join(MODELS_DIR, 'le.pkl'))
    
    with open(os.path.join(MODELS_DIR, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)
        
    print("Fine-tuning phase complete!")

if __name__ == '__main__':
    main()
