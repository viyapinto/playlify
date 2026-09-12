import os
import cv2
import glob
import torch
import numpy as np
import pandas as pd
from tqdm import tqdm
from PIL import Image
import torchvision.transforms as transforms
import torchvision.models as models
import torch.nn as nn

# Configuration
IMAGE_DIR = 'data/images'
OUTPUT_FILE = 'data/extracted_features.parquet'
BATCH_SIZE = 128

# Setup Device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

def get_mobilenet_model():
    print("Loading MobileNetV2...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    # Replace the classifier with Identity to get the 1280-dim feature vector
    model.classifier = nn.Identity()
    model = model.to(device)
    model.eval()
    return model

# Transforms for MobileNetV2
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def extract_interpretable_features(img_path):
    # Load image with OpenCV (BGR)
    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        return None
    
    # Resize for faster computation
    img_bgr = cv2.resize(img_bgr, (224, 224))
    
    # 1. Color Histogram (HSV)
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([img_hsv], [0, 1, 2], None, [8, 8, 8],
                        [0, 180, 0, 256, 0, 256])
    cv2.normalize(hist, hist)
    hist_features = hist.flatten()
    
    # 2. Image Statistics
    # BGR means and stds
    means, stds = cv2.meanStdDev(img_bgr)
    b_mean, g_mean, r_mean = means.flatten()
    b_std, g_std, r_std = stds.flatten()
    
    # Brightness and contrast (from V channel)
    v_channel = img_hsv[:,:,2]
    brightness = np.mean(v_channel)
    contrast = np.std(v_channel)
    
    stats_features = np.array([r_mean, g_mean, b_mean, r_std, g_std, b_std, brightness, contrast])
    
    return np.concatenate([hist_features, stats_features])

def main():
    model = get_mobilenet_model()
    
    # Find all images
    image_paths = glob.glob(os.path.join(IMAGE_DIR, '*.jpg'))
    print(f"Found {len(image_paths)} images.")
    
    all_features = []
    
    # Process in batches for the deep learning model
    for i in tqdm(range(0, len(image_paths), BATCH_SIZE), desc="Extracting features"):
        batch_paths = image_paths[i:i+BATCH_SIZE]
        batch_indices = []
        batch_tensors = []
        batch_interp = []
        
        for path in batch_paths:
            try:
                # Extract interpretable features
                interp_feats = extract_interpretable_features(path)
                if interp_feats is None:
                    continue
                
                # Load for deep features
                img = Image.open(path).convert('RGB')
                tensor = transform(img)
                
                # Get album index from filename
                idx = int(os.path.basename(path).split('.')[0])
                
                batch_indices.append(idx)
                batch_tensors.append(tensor)
                batch_interp.append(interp_feats)
            except Exception as e:
                print(f"Error processing {path}: {e}")
                
        if not batch_tensors:
            continue
            
        # Deep Feature Extraction
        batch_tensors = torch.stack(batch_tensors).to(device)
        with torch.no_grad():
            deep_feats = model(batch_tensors).cpu().numpy()
            
        # Combine everything
        for idx, interp_f, deep_f in zip(batch_indices, batch_interp, deep_feats):
            # Create a dictionary for the row
            row = {'album_index': idx}
            
            # Add interpretable features
            for j, val in enumerate(interp_f[:512]):
                row[f'hist_{j}'] = val
            row['r_mean'] = interp_f[512]
            row['g_mean'] = interp_f[513]
            row['b_mean'] = interp_f[514]
            row['r_std'] = interp_f[515]
            row['g_std'] = interp_f[516]
            row['b_std'] = interp_f[517]
            row['brightness'] = interp_f[518]
            row['contrast'] = interp_f[519]
            
            # Add deep features
            for j, val in enumerate(deep_f):
                row[f'mobilenet_{j}'] = val
                
            all_features.append(row)
            
    # Save to DataFrame and Parquet
    print(f"Saving extracted features for {len(all_features)} images...")
    df = pd.DataFrame(all_features)
    df.to_parquet(OUTPUT_FILE, index=False)
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
