import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import classification_report, accuracy_score

# Configuration
LABELS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'cleaned_album_dataset.tsv')
FEATURES_FILE = 'data/extracted_features.parquet'
MODELS_DIR = 'models'
KNN_PCA_COMPONENTS = 128

def main():
    print("Loading data...")
    labels_df = pd.read_csv(LABELS_FILE, sep='\t')
    features_df = pd.read_parquet(FEATURES_FILE)

    df = pd.merge(labels_df, features_df, on='album_index', how='inner')
    print(f"Total merged records: {len(df)}")
    
    train_df = df[df['set'] == 'train']
    val_df = df[df['set'] == 'val']
    test_df = df[df['set'] == 'test']
    
    print(f"Train size: {len(train_df)}, Val size: {len(val_df)}, Test size: {len(test_df)}")
    
    meta_cols = ['album_index', 'genre', 'set', 'msd_artist_id', 'image_url', 'original_track_count']
    feature_cols = [c for c in df.columns if c not in meta_cols]
    
    X_train = train_df[feature_cols].values
    y_train_str = train_df['genre'].values
    
    X_val = val_df[feature_cols].values
    y_val_str = val_df['genre'].values
    
    X_test = test_df[feature_cols].values
    y_test_str = test_df['genre'].values
    
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    # Fit on all genres to prevent unseen label errors
    le.fit(df['genre'].values)
    y_train = le.transform(y_train_str)
    y_val = le.transform(y_val_str)
    y_test = le.transform(y_test_str)
    
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    print("\n--- Training MLP Neural Network (All Features) ---")
    mlp = MLPClassifier(
        hidden_layer_sizes=(512, 256),
        max_iter=500,
        early_stopping=True,
        random_state=42
    )
    mlp.fit(X_train_scaled, y_train)
    mlp_val_preds = mlp.predict(X_val_scaled)
    mlp_val_acc = accuracy_score(y_val, mlp_val_preds)
    print(f"MLP Validation Accuracy: {mlp_val_acc:.4f}")
    
    print("\n--- Training Logistic Regression Baseline (All Features) ---")
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    lr_val_preds = lr.predict(X_val_scaled)
    lr_val_acc = accuracy_score(y_val, lr_val_preds)
    print(f"LR Validation Accuracy: {lr_val_acc:.4f}")
    
    if mlp_val_acc >= lr_val_acc:
        best_model = mlp
        best_name = "MLP Neural Network"
    else:
        best_model = lr
        best_name = "Logistic Regression"
        
    print(f"\nSelected Best Model: {best_name}")
    
    print("\n--- Test Set Evaluation ---")
    test_preds = best_model.predict(X_test_scaled)
    print(classification_report(y_test, test_preds, labels=range(len(le.classes_)), target_names=le.classes_))
    
    # We still use PCA for the NearestNeighbors index to make similarity search fast
    print(f"\nApplying PCA (components={KNN_PCA_COMPONENTS}) for Similarity Search Index...")
    pca = PCA(n_components=KNN_PCA_COMPONENTS, random_state=42)
    X_all_scaled = scaler.transform(df[feature_cols].values)
    X_all_pca = pca.fit_transform(X_all_scaled)
    
    print("Building NearestNeighbors index...")
    knn = NearestNeighbors(n_neighbors=10, metric='cosine', n_jobs=-1)
    knn.fit(X_all_pca)
    
    metadata = []
    for idx, row in df.iterrows():
        metadata.append({
            'album_index': int(row['album_index']),
            'genre': row['genre'],
            'artist_id': row['msd_artist_id'],
            'image_url': row['image_url']
        })
        
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("Saving models and metadata to disk...")
    
    joblib.dump(scaler, os.path.join(MODELS_DIR, 'scaler.pkl'))
    joblib.dump(pca, os.path.join(MODELS_DIR, 'pca.pkl'))
    joblib.dump(le, os.path.join(MODELS_DIR, 'le.pkl'))
    joblib.dump(best_model, os.path.join(MODELS_DIR, 'classifier.pkl'))
    joblib.dump(knn, os.path.join(MODELS_DIR, 'knn.pkl'))
    
    with open(os.path.join(MODELS_DIR, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)
        
    print("Modeling phase complete!")

if __name__ == '__main__':
    main()
