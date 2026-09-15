import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
DATASET_FILE = os.path.join(os.path.dirname(__file__), 'data', 'final_album_dataset.tsv')
FEATURES_FILE = 'data/extracted_features.parquet'
OUTPUT_DIR = 'research/eda_output'

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load dataset
    print("Loading dataset...")
    df = pd.read_csv(DATASET_FILE, sep='\t')
    
    # Load features
    print("Loading extracted features...")
    if not os.path.exists(FEATURES_FILE):
        print(f"Error: {FEATURES_FILE} not found. Please run phase3_feature_extractor.py first.")
        return
    features = pd.read_parquet(FEATURES_FILE)
    
    # Merge datasets
    print("Merging datasets...")
    merged = pd.merge(df, features, on='album_index')
    print(f"Merged dataset shape: {merged.shape}")
    
    # 1. Class Distribution
    print("Plotting Class Distribution...")
    plt.figure(figsize=(12, 6))
    genre_counts = merged['genre'].value_counts()
    sns.barplot(x=genre_counts.index, y=genre_counts.values)
    plt.title('Distribution of Musical Genres in Dataset')
    plt.xlabel('Genre')
    plt.ylabel('Number of Albums')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'class_distribution.png'))
    plt.close()
    
    # 2. Color Distribution by Genre (Brightness and Contrast)
    print("Plotting Brightness & Contrast by Genre...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    sns.boxplot(x='genre', y='brightness', data=merged, ax=ax1)
    ax1.set_title('Image Brightness by Genre')
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
    
    sns.boxplot(x='genre', y='contrast', data=merged, ax=ax2)
    ax2.set_title('Image Contrast by Genre')
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'color_distribution.png'))
    plt.close()
    
    # Mean RGB by Genre
    print("Plotting RGB means by Genre...")
    rgb_means = merged.groupby('genre')[['r_mean', 'g_mean', 'b_mean']].mean()
    rgb_means.plot(kind='bar', figsize=(12, 6), color=['red', 'green', 'blue'])
    plt.title('Average RGB Values by Genre')
    plt.xlabel('Genre')
    plt.ylabel('Mean Color Value')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'rgb_means.png'))
    plt.close()
    
    # 3. Feature Variance (Deep Features)
    print("Analyzing Deep Feature Variance...")
    mobilenet_cols = [col for col in merged.columns if col.startswith('mobilenet_')]
    if mobilenet_cols:
        variances = merged[mobilenet_cols].var()
        top_variances = variances.sort_values(ascending=False).head(20)
        
        plt.figure(figsize=(12, 6))
        top_variances.plot(kind='bar')
        plt.title('Top 20 MobileNet Features by Variance')
        plt.xlabel('MobileNet Feature Index')
        plt.ylabel('Variance')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'feature_variance.png'))
        plt.close()
        
    print(f"EDA complete! Visualizations saved to {OUTPUT_DIR}/")

if __name__ == '__main__':
    main()
