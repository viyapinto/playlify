import os
import json
import joblib
import torch
import torch.nn as nn
import numpy as np
from torchvision import models, transforms
from PIL import Image
import io
import gc
import psutil

def get_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

class PlaylifyModel:
    def __init__(self, models_dir: str):
        self.device = torch.device("cpu") # Force CPU to save memory on Render Free Tier
        print(f"Initializing inference engine on {self.device}...")
        print(f"[MEMORY] Startup RSS: {get_memory_mb():.2f} MB")
        
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
        
        # Load weights without keeping checkpoint in memory
        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(checkpoint)
        del checkpoint
        gc.collect()
        
        self.feature_extractor = self.model.features
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier_head = self.model.classifier
        
        self.model.eval()
        for param in self.model.parameters():
            param.requires_grad = False
            
        print(f"[MEMORY] RSS after MobileNetV2: {get_memory_mb():.2f} MB")
        
        # 3. Load PCA and KNN
        print("Loading PCA & extracting KNN array...")
        self.pca = joblib.load(self.pca_path)
        
        # Extract purely the raw numpy array from the NearestNeighbors object to save huge memory overhead
        knn_obj = joblib.load(self.knn_path)
        self.knn_features = np.array(knn_obj._fit_X, dtype=np.float32)
        del knn_obj
        gc.collect()
        
        print(f"[MEMORY] RSS after PCA/KNN: {get_memory_mb():.2f} MB")
        
        # 4. Load Metadata Lookup
        print("Loading Metadata...")
        with open(self.metadata_path, 'r') as f:
            raw_metadata = json.load(f)
            
        # Only keep necessary fields to minimize dictionary overhead
        self.metadata = [
            {
                "album_index": item["album_index"], 
                "genre": item["genre"],
                "artist_id": item["artist_id"],
                "image_url": item["image_url"]
            } for item in raw_metadata
        ]
        
        from collections import Counter
        counts = Counter([item["genre"] for item in self.metadata])
        total = sum(counts.values())
        priors = [counts.get(c, 1) / total for c in self.le.classes_]
        self.class_priors = torch.tensor(priors, dtype=torch.float32, device=self.device)
        
        del raw_metadata
        gc.collect()
        
        print(f"[MEMORY] RSS after metadata: {get_memory_mb():.2f} MB")
        print("Initialization complete.")
        
    @torch.inference_mode()
    def predict(self, image_bytes: bytes, num_neighbors: int = 10):
        print(f"[MEMORY] RSS before prediction: {get_memory_mb():.2f} MB")
        
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception as e:
            raise ValueError("Invalid image file.") from e
            
        img_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # 1. Extract raw features
        features = self.feature_extractor(img_tensor)
        
        # 2. Pool and flatten
        pooled = self.pool(features)
        flattened = torch.flatten(pooled, 1)
        
        # 3. Get classification output
        logits = self.classifier_head(flattened)
        raw_probabilities = torch.nn.functional.softmax(logits, dim=1)[0]
        
        # Apply inference-time prior shift
        adjusted_probs = raw_probabilities / self.class_priors
        probabilities = adjusted_probs / adjusted_probs.sum()
            
        # Get top prediction
        prob, class_idx = torch.max(probabilities, 0)
        predicted_genre = self.le.inverse_transform([class_idx.item()])[0]
        confidence = prob.item()
        
        all_probs = {
            self.le.inverse_transform([i])[0]: p.item() 
            for i, p in enumerate(probabilities)
        }
        
        # 4. Get similar albums using highly efficient numpy cosine distance
        features_np = flattened.cpu().numpy().astype(np.float32)
        features_pca = self.pca.transform(features_np)[0] # Shape (128,)
        
        # Cosine distance: 1 - (A.B / (|A|*|B|))
        # self.knn_features is (16595, 128)
        norm_pca = np.linalg.norm(features_pca)
        norms_db = np.linalg.norm(self.knn_features, axis=1)
        
        # Avoid division by zero
        norm_pca = norm_pca if norm_pca > 0 else 1e-10
        norms_db = np.where(norms_db > 0, norms_db, 1e-10)
        
        # Compute dot products
        dot_products = np.dot(self.knn_features, features_pca)
        
        # Compute cosine distances
        cosine_distances = 1.0 - (dot_products / (norms_db * norm_pca))
        
        # Get top k smallest distances
        # argpartition is O(N) rather than O(N log N) for full sort
        if num_neighbors < len(cosine_distances):
            indices = np.argpartition(cosine_distances, num_neighbors)[:num_neighbors]
            # sort the top k exactly
            sub_sort = np.argsort(cosine_distances[indices])
            indices = indices[sub_sort]
        else:
            indices = np.argsort(cosine_distances)
            
        distances = cosine_distances[indices]
        
        similar_albums = []
        for i, idx in enumerate(indices):
            album_info = self.metadata[idx]
            similar_albums.append({
                "album_index": album_info["album_index"],
                "genre": album_info["genre"],
                "artist_id": album_info["artist_id"],
                "image_url": album_info["image_url"],
                "distance": float(distances[i])
            })
            
        if similar_albums and similar_albums[0]["distance"] < 0.05:
            predicted_genre = similar_albums[0]["genre"]
            confidence = 1.0
            for g in all_probs:
                all_probs[g] = 1.0 if g == predicted_genre else 0.0
                
        # Force cleanup of request-level large objects
        del img_tensor, features, pooled, flattened, logits, raw_probabilities, probabilities
        gc.collect()
        
        print(f"[MEMORY] RSS after prediction: {get_memory_mb():.2f} MB")
        
        return {
            "prediction": {
                "genre": predicted_genre,
                "confidence": confidence,
                "all_probabilities": all_probs
            },
            "similar_albums": similar_albums
        }
