import os
import pandas as pd

def analyze_conflicts(file_path):
    df = pd.read_csv(file_path, sep='\t')
    
    # 1. Genre conflicts
    # Group by album_index and count unique genres
    album_genres = df.groupby('album_index')['genre'].nunique()
    conflicting_albums = album_genres[album_genres > 1]
    print(f"Albums with conflicting genres: {len(conflicting_albums)}")
    
    # Let's see some examples
    if len(conflicting_albums) > 0:
        sample_conflicts = conflicting_albums.index[:5]
        for idx in sample_conflicts:
            print(f"\nAlbum Index: {idx}")
            print(df[df['album_index'] == idx][['msd_track_id', 'genre', 'image_url']])
            
    # 2. Split conflicts
    # Group by album_index and count unique splits
    album_splits = df.groupby('album_index')['set'].nunique()
    conflicting_splits = album_splits[album_splits > 1]
    print(f"\nAlbums in multiple splits (Train/Val/Test leakage): {len(conflicting_splits)}")
    
    # 3. Multiple URLs
    album_urls = df.groupby('album_index')['image_url'].nunique()
    multi_url_albums = album_urls[album_urls > 1]
    print(f"\nAlbums with multiple URLs: {len(multi_url_albums)}")
    
    if len(multi_url_albums) > 0:
        sample_multi = multi_url_albums.index[:5]
        for idx in sample_multi:
            print(f"\nAlbum Index: {idx}")
            print(df[df['album_index'] == idx][['msd_track_id', 'genre', 'image_url']])

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', '1240485', 'MSD-I_dataset.tsv')
    analyze_conflicts(file_path)
