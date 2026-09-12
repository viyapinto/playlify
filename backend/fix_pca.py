import os
import json
import joblib
import torch
import torch.nn as nn
from torchvision import models, transforms
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from PIL import Image
import numpy as np

MODELS_DIR = '../models'
IMAGE_DIR = '../data/images'
KNN_PCA_COMPONENTS = 128

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def main():
    print(f"Using device: {device}")
    
    # Load Label Encoder to get num_classes
    le = joblib.load(os.path.join(MODELS_DIR, 'le.pkl'))
    num_classes = len(le.classes_)
    
    # Initialize Model
    print("Initializing MobileNetV2...")
    model = models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    
    # Load finetuned weights
    model.load_state_dict(torch.load(os.path.join(MODELS_DIR, 'finetuned_model.pth'), map_location=device, weights_only=True))
    
    # Remove classification head to get embeddings
    model.classifier = nn.Identity()
    model = model.to(device)
    model.eval()

    # Transforms
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    print("Loading Metadata...")
    with open(os.path.join(MODELS_DIR, 'metadata.json'), 'r') as f:
        metadata = json.load(f)

    all_features = []
    
    print("Extracting features from all images...")
    with torch.no_grad():
        for i, item in enumerate(metadata):
            img_path = os.path.join(IMAGE_DIR, f"{item['album_index']}.jpg")
            try:
                image = Image.open(img_path).convert('RGB')
            except Exception:
                image = Image.new('RGB', (224, 224))
                
            img_tensor = transform(image).unsqueeze(0).to(device)
            features = model(img_tensor)
            all_features.append(features.cpu().numpy()[0])
            
            if (i+1) % 500 == 0:
                print(f"Processed {i+1}/{len(metadata)}")

    all_features = np.array(all_features)
    print(f"Feature shape: {all_features.shape}")
    
    print(f"Applying PCA (components={KNN_PCA_COMPONENTS})...")
    pca = PCA(n_components=KNN_PCA_COMPONENTS, random_state=42)
    features_pca = pca.fit_transform(all_features)
    
    print("Building NearestNeighbors index...")
    knn = NearestNeighbors(n_neighbors=10, metric='cosine', n_jobs=-1)
    knn.fit(features_pca)
    
    print("Saving updated PCA and KNN to disk...")
    joblib.dump(pca, os.path.join(MODELS_DIR, 'pca.pkl'))
    joblib.dump(knn, os.path.join(MODELS_DIR, 'knn.pkl'))
    print("Done!")

if __name__ == '__main__':
    main()
