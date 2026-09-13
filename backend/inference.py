import os
import json
import joblib
import torch
import torch.nn as nn
import numpy as np
from torchvision import models, transforms
from PIL import Image
import io

class PlaylifyModel:
    def __init__(self, models_dir: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Initializing inference engine on {self.device}...")
        
        # Paths
        self.model_path = os.path.join(models_dir, 'finetuned_model.pth')
        self.pca_path = os.path.join(models_dir, 'pca.pkl')
        self.knn_path = os.path.join(models_dir, 'knn.pkl')
        self.le_path = os.path.join(models_dir, 'le.pkl')
        self.metadata_path = os.path.join(models_dir, 'metadata.json')
        
        # Load transformations
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self._load_artifacts()
        
    def _load_artifacts(self):
        # 1. Load Label Encoder
        print("Loading Label Encoder...")
        self.le = joblib.load(self.le_path)
        num_classes = len(self.le.classes_)
        
        # 2. Load PyTorch Model
        print("Loading MobileNetV2...")
        self.model = models.mobilenet_v2(weights=None)
        in_features = self.model.classifier[1].in_features
        self.model.classifier[1] = nn.Linear(in_features, num_classes)
        self.model.load_state_dict(torch.load(self.model_path, map_location=self.device, weights_only=True))
        
        # Split model into feature extractor and classifier
        # This allows us to do a single forward pass
        self.feature_extractor = self.model.features
        # MobileNetV2 uses adaptive avg pool + flatten before the classifier
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier_head = self.model.classifier
        
        self.model.eval()
        self.model = self.model.to(self.device)
        
        # 3. Load PCA and KNN
        print("Loading PCA & KNN...")
        self.pca = joblib.load(self.pca_path)
        self.knn = joblib.load(self.knn_path)
        
        # 4. Load Metadata Lookup
        print("Loading Metadata...")
        with open(self.metadata_path, 'r') as f:
            self.metadata = json.load(f)
            
        # 5. Compute Class Priors for inference-time adjustment
        from collections import Counter
        counts = Counter([item["genre"] for item in self.metadata])
        total = sum(counts.values())
        
        # Create a tensor of priors matching the label encoder order
        priors = [counts.get(c, 1) / total for c in self.le.classes_]
        self.class_priors = torch.tensor(priors, dtype=torch.float32, device=self.device)
            
        print("Initialization complete.")
        
    def predict(self, image_bytes: bytes, num_neighbors: int = 10):
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception as e:
            raise ValueError("Invalid image file.") from e
            
        img_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            # 1. Extract raw features (N, C, H, W)
            features = self.feature_extractor(img_tensor)
            
            # 2. Pool and flatten for the classifier head
            pooled = self.pool(features)
            flattened = torch.flatten(pooled, 1) # This is what PCA was trained on
            
            # 3. Get classification output
            logits = self.classifier_head(flattened)
            raw_probabilities = torch.nn.functional.softmax(logits, dim=1)[0]
            
            # Apply inference-time prior shift to unbias predictions
            adjusted_probs = raw_probabilities / self.class_priors
            probabilities = adjusted_probs / adjusted_probs.sum()
            
        # Get top prediction
        prob, class_idx = torch.max(probabilities, 0)
        predicted_genre = self.le.inverse_transform([class_idx.item()])[0]
        confidence = prob.item()
        
        # Format all probabilities
        all_probs = {
            self.le.inverse_transform([i])[0]: p.item() 
            for i, p in enumerate(probabilities)
        }
        
        # Get similar albums
        features_np = flattened.cpu().numpy()
        features_pca = self.pca.transform(features_np)
        distances, indices = self.knn.kneighbors(features_pca, n_neighbors=num_neighbors)
        
        similar_albums = []
        for i, idx in enumerate(indices[0]):
            # The indices returned by KNN correspond directly to the row index in metadata
            album_info = self.metadata[idx]
            similar_albums.append({
                "album_index": album_info["album_index"],
                "genre": album_info["genre"],
                "artist_id": album_info["artist_id"],
                "image_url": album_info["image_url"],
                "distance": float(distances[0][i])
            })
            
        # EXACT MATCH OVERRIDE
        # If the closest album has a distance of < 0.05, it's the exact same image
        # (relaxed from 1e-4 to account for JPEG compression/resizing on upload).
        if similar_albums and similar_albums[0]["distance"] < 0.05:
            predicted_genre = similar_albums[0]["genre"]
            confidence = 1.0
            # Reset probabilities to 100% for the matched genre
            for g in all_probs:
                all_probs[g] = 1.0 if g == predicted_genre else 0.0
            
        return {
            "prediction": {
                "genre": predicted_genre,
                "confidence": confidence,
                "all_probabilities": all_probs
            },
            "similar_albums": similar_albums
        }
