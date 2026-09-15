import os
import json
import joblib
import pandas as pd
import numpy as np

# Config
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DATA_DIR = os.path.join(ROOT_DIR, 'frontend', 'public', 'data')
os.makedirs(FRONTEND_DATA_DIR, exist_ok=True)

print("Loading dataset and features...")
df_features = pd.read_parquet(os.path.join(ROOT_DIR, 'data', 'extracted_features.parquet'))
df_meta = pd.read_csv(os.path.join(ROOT_DIR, 'research', 'data', 'final_album_dataset.tsv'), sep='\t')

# Ensure album_index alignment
df = pd.merge(df_meta, df_features, on='album_index')

print("1. Generating PCA data...")
# Load PCA
pca = joblib.load(os.path.join(ROOT_DIR, 'models', 'pca.pkl'))
# MobileNet features
mobilenet_cols = [f'mobilenet_{i}' for i in range(1280)]
X = df[mobilenet_cols].values

# We only want the first 2 components for the frontend 2D plot
# Note: we should project it first to ensure it's aligned with how pca.pkl transforms data
X_pca = pca.transform(X)

# Sample 40 per genre to keep it lightweight (40 * 15 = 600 points)
# For front-end interactivity without lag
df['pca_x'] = X_pca[:, 0]
df['pca_y'] = X_pca[:, 1]

sampled_pca = []
for genre in df['genre'].unique():
    genre_df = df[df['genre'] == genre]
    sample_size = min(40, len(genre_df))
    sampled_df = genre_df.sample(n=sample_size, random_state=42)
    for _, row in sampled_df.iterrows():
        sampled_pca.append({
            "id": row['msd_artist_id'] + "_" + str(row['album_index']),
            "genre": row['genre'],
            "x": float(row['pca_x']),
            "y": float(row['pca_y']),
            "image_url": row['image_url']
        })

with open(os.path.join(FRONTEND_DATA_DIR, 'pca_data.json'), 'w') as f:
    json.dump(sampled_pca, f)
print("Saved pca_data.json")

print("2. Generating Genre Profiles (Visual DNA)...")
# From phase3_feature_extractor.py:
# stats_features = np.array([r_mean, g_mean, b_mean, r_std, g_std, b_std, brightness, contrast])
# In the parquet file, these were concatenated after hist_features (512 dims)
# So indices 512 to 519 are the stats features.
stats_cols = ['r_mean', 'g_mean', 'b_mean', 'r_std', 'g_std', 'b_std', 'brightness', 'contrast']

profiles = []
for genre in df['genre'].unique():
    genre_df = df[df['genre'] == genre]
    
    # Calculate means
    genre_stats = genre_df[stats_cols].mean().values
    
    r_mean, g_mean, b_mean = genre_stats[0:3]
    brightness = genre_stats[6]
    contrast = genre_stats[7]
    
    profiles.append({
        "genre": genre,
        "sample_size": len(genre_df),
        "r_mean": float(r_mean),
        "g_mean": float(g_mean),
        "b_mean": float(b_mean),
        "brightness": float(brightness),
        "contrast": float(contrast)
    })

# Sort alphabetically by genre
profiles = sorted(profiles, key=lambda x: x['genre'])

with open(os.path.join(FRONTEND_DATA_DIR, 'genre_profiles.json'), 'w') as f:
    json.dump(profiles, f)
print("Saved genre_profiles.json")

print("3. Generating Confusion Matrix...")
# Extract directly from baseline_results.json
with open(os.path.join(ROOT_DIR, 'research', 'results', 'baseline_results.json'), 'r') as f:
    baseline = json.load(f)

# Genres in order
le = joblib.load(os.path.join(ROOT_DIR, 'models', 'le.pkl'))
genres = list(le.classes_)

matrix_data = {
    "accuracy": baseline["accuracy"],
    "macro_f1": baseline["macro_f1"],
    "weighted_f1": baseline["weighted_f1"],
    "genres": genres,
    "matrix": baseline["confusion_matrix"]
}

with open(os.path.join(FRONTEND_DATA_DIR, 'confusion_matrix.json'), 'w') as f:
    json.dump(matrix_data, f)
print("Saved confusion_matrix.json")

print("Data generation complete!")
