import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import imagehash
import os
import json

def get_image_hash(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return imagehash.average_hash(img)
    except Exception as e:
        print(f"Error downloading/hashing {url}: {e}")
        return None

def clean_dataset(input_file, output_file, stats_file):
    print("Loading dataset...")
    df = pd.read_csv(input_file, sep='\t')
    original_tracks = len(df)
    original_albums = df['album_index'].nunique()
    
    print(f"Original tracks: {original_tracks}")
    print(f"Original albums: {original_albums}")
    
    # Track-to-album mapping setup
    albums = {}
    
    # 1. Detect Genre Conflicts
    print("Detecting genre conflicts...")
    album_genres = df.groupby('album_index')['genre'].nunique()
    conflicting_genres = album_genres[album_genres > 1].index.tolist()
    print(f"Albums with conflicting genres (to be excluded): {len(conflicting_genres)}")
    
    # Filter out conflicting genres
    df = df[~df['album_index'].isin(conflicting_genres)]
    
    # 2. Detect and Resolve Split Leakage
    print("Resolving split leakage...")
    album_splits = df.groupby('album_index')['set'].nunique()
    conflicting_splits = album_splits[album_splits > 1].index.tolist()
    print(f"Albums spanning multiple splits: {len(conflicting_splits)}")
    
    # Function to resolve split
    def resolve_split(album_idx, subset_df):
        split_counts = subset_df['set'].value_counts()
        max_count = split_counts.max()
        # Get splits with max_count
        top_splits = split_counts[split_counts == max_count].index.tolist()
        if 'train' in top_splits: return 'train'
        if 'val' in top_splits: return 'val'
        if 'test' in top_splits: return 'test'
        return top_splits[0]

    split_resolutions = {}
    for idx in conflicting_splits:
        split_resolutions[idx] = resolve_split(idx, df[df['album_index'] == idx])
    
    # 3. Detect and Resolve Multiple Image URLs
    print("Resolving multiple image URLs per album...")
    album_urls = df.groupby('album_index')['image_url'].nunique()
    multi_url_albums = album_urls[album_urls > 1].index.tolist()
    print(f"Albums with multiple distinct URLs: {len(multi_url_albums)}")
    
    url_exclusions = []
    url_resolutions = {}
    
    for idx in multi_url_albums:
        urls = df[df['album_index'] == idx]['image_url'].unique()
        hashes = []
        valid_urls = []
        for url in urls:
            h = get_image_hash(url)
            if h is not None:
                hashes.append(h)
                valid_urls.append(url)
                
        if not hashes:
            url_exclusions.append(idx)
        else:
            # Check if hashes are visually similar (hash difference <= 2)
            all_similar = True
            base_hash = hashes[0]
            for h in hashes[1:]:
                if base_hash - h > 2:
                    all_similar = False
                    break
            if all_similar:
                url_resolutions[idx] = valid_urls[0]
            else:
                print(f"Visual difference detected for album {idx}. Excluding.")
                url_exclusions.append(idx)
                
    print(f"Albums excluded due to distinct multi-URL images: {len(url_exclusions)}")
    
    # Filter out multi-url exclusions
    df = df[~df['album_index'].isin(url_exclusions)]
    
    # 4. Construct Final Album-Level Dataset
    print("Constructing final album-level dataset...")
    
    final_records = []
    
    for album_idx, group in df.groupby('album_index'):
        # Get genre (already guaranteed to be 1 unique value)
        genre = group['genre'].iloc[0]
        
        # Get artist (can be multiple, we take the first or compile them. Let's take the first for simplicity, or the one most frequent)
        artist = group['msd_artist_id'].mode().iloc[0]
        
        # Get split
        if album_idx in split_resolutions:
            split = split_resolutions[album_idx]
        else:
            split = group['set'].iloc[0]
            
        # Get image URL
        if album_idx in url_resolutions:
            url = url_resolutions[album_idx]
        else:
            url = group['image_url'].iloc[0]
            
        final_records.append({
            'album_index': album_idx,
            'genre': genre,
            'set': split,
            'msd_artist_id': artist,
            'image_url': url,
            'original_track_count': len(group)
        })
        
    final_df = pd.DataFrame(final_records)
    
    final_albums = len(final_df)
    print(f"Final album count: {final_albums}")
    
    # Save datasets
    final_df.to_csv(output_file, index=False, sep='\t')
    
    # Save stats
    stats = {
        'original_tracks': original_tracks,
        'original_albums': original_albums,
        'final_albums': final_albums,
        'genre_conflicts_excluded': len(conflicting_genres),
        'split_conflicts_resolved': len(conflicting_splits),
        'multi_url_cases': len(multi_url_albums),
        'multi_url_excluded': len(url_exclusions),
        'final_genre_distribution': final_df['genre'].value_counts().to_dict(),
        'final_split_counts': final_df['set'].value_counts().to_dict()
    }
    
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
        
    print(f"Cleaned dataset saved to {output_file}")
    print(f"Stats saved to {stats_file}")

if __name__ == "__main__":
    input_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', '1240485', 'MSD-I_dataset.tsv')
    output_file = os.path.join(os.path.dirname(__file__), 'data', 'cleaned_album_dataset.tsv')
    stats_file = "phase2_cleaning_stats.json"
    clean_dataset(input_file, output_file, stats_file)
