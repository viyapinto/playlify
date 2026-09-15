import os
import pandas as pd

def check_dataset():
    labels_file = os.path.join(os.path.dirname(__file__), 'data', 'cleaned_album_dataset.tsv')
    image_dir = 'data/images'
    
    print("--- DATASET INTEGRITY CHECK ---")
    df = pd.read_csv(labels_file, sep='\t')
    print(f"Total rows in metadata: {len(df)}")
    
    # 1. Check for duplicates
    dup_albums = df.duplicated(subset=['album_index']).sum()
    print(f"Duplicate album_index count: {dup_albums}")
    
    dup_images = df.duplicated(subset=['image_url']).sum()
    print(f"Duplicate image_url count: {dup_images}")
    
    # 2. Check for missing images
    missing_count = 0
    valid_indices = []
    for idx in df['album_index']:
        if os.path.exists(os.path.join(image_dir, f"{idx}.jpg")):
            valid_indices.append(idx)
        else:
            missing_count += 1
            
    print(f"Missing image files: {missing_count}")
    df_valid = df[df['album_index'].isin(valid_indices)]
    
    # 3. Class distribution
    print("\nClass Distribution (Valid Images):")
    print(df_valid['genre'].value_counts())
    
    # 4. Train/Val/Test split and leakage
    train_albums = set(df_valid[df_valid['set'] == 'train']['album_index'])
    val_albums = set(df_valid[df_valid['set'] == 'val']['album_index'])
    test_albums = set(df_valid[df_valid['set'] == 'test']['album_index'])
    
    print(f"\nSplit sizes - Train: {len(train_albums)}, Val: {len(val_albums)}, Test: {len(test_albums)}")
    
    leakage_train_val = train_albums.intersection(val_albums)
    leakage_train_test = train_albums.intersection(test_albums)
    leakage_val_test = val_albums.intersection(test_albums)
    
    print(f"Leakage (Train & Val): {len(leakage_train_val)}")
    print(f"Leakage (Train & Test): {len(leakage_train_test)}")
    print(f"Leakage (Val & Test): {len(leakage_val_test)}")

if __name__ == '__main__':
    check_dataset()
