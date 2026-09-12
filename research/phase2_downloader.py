import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import os
import concurrent.futures
import time
import json
import logging

def validate_image(content):
    try:
        img = Image.open(BytesIO(content))
        img.verify()
        return True
    except Exception:
        return False

def download_image(url, save_path, max_retries=3, timeout=10):
    if os.path.exists(save_path):
        # Already downloaded, check if valid
        try:
            with open(save_path, 'rb') as f:
                if validate_image(f.read()):
                    return "SKIPPED_ALREADY_EXISTS"
        except Exception:
            pass # Try downloading again if invalid
            
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            if validate_image(response.content):
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return "SUCCESS"
            else:
                if attempt == max_retries - 1:
                    return "ERROR_CORRUPT"
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                return f"ERROR_NETWORK_{e.__class__.__name__}"
            time.sleep(1)
            
    return "ERROR_MAX_RETRIES"

def process_row(row, img_dir):
    idx = row['album_index']
    url = row['image_url']
    save_path = os.path.join(img_dir, f"{idx}.jpg")
    
    if pd.isna(url) or not url:
        return idx, "ERROR_MISSING_URL"
        
    status = download_image(url, save_path)
    return idx, status

def run_downloader(input_file, output_file, stats_file, log_file, img_dir):
    os.makedirs(img_dir, exist_ok=True)
    
    # Setup logging
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
    
    print("Loading cleaned dataset...")
    df = pd.read_csv(input_file, sep='\t')
    total_requested = len(df)
    
    print(f"Starting download of {total_requested} images...")
    results = {}
    
    # We use ThreadPoolExecutor because this is an I/O bound task
    max_workers = 20
    completed = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_idx = {executor.submit(process_row, row, img_dir): row['album_index'] for _, row in df.iterrows()}
        
        for future in concurrent.futures.as_completed(future_to_idx):
            idx, status = future.result()
            results[idx] = status
            completed += 1
            if completed % 500 == 0:
                print(f"Progress: {completed}/{total_requested}...")
                
            logging.info(f"Album {idx}: {status}")
            
    # Compile statistics
    status_counts = pd.Series(list(results.values())).value_counts().to_dict()
    successful = sum(1 for status in results.values() if status in ["SUCCESS", "SKIPPED_ALREADY_EXISTS"])
    failed = total_requested - successful
    
    print("\nDownload Summary:")
    print(f"Total requested: {total_requested}")
    print(f"Successful/Valid: {successful}")
    print(f"Failed/Corrupt/Missing: {failed}")
    for k, v in status_counts.items():
        print(f" - {k}: {v}")
        
    # Filter dataset
    valid_indices = [idx for idx, status in results.items() if status in ["SUCCESS", "SKIPPED_ALREADY_EXISTS"]]
    final_df = df[df['album_index'].isin(valid_indices)]
    
    print(f"\nSaving final dataset with {len(final_df)} records...")
    final_df.to_csv(output_file, index=False, sep='\t')
    
    # Save final statistics
    final_stats = {
        'total_requested': total_requested,
        'successful_images': successful,
        'failed_images': failed,
        'status_breakdown': status_counts,
        'final_genre_distribution': final_df['genre'].value_counts().to_dict(),
        'final_split_counts': final_df['set'].value_counts().to_dict()
    }
    
    with open(stats_file, 'w') as f:
        json.dump(final_stats, f, indent=4)
        
    print(f"Final dataset saved to {output_file}")
    print(f"Stats saved to {stats_file}")

if __name__ == "__main__":
    input_file = "cleaned_album_dataset.tsv"
    output_file = "final_album_dataset.tsv"
    stats_file = "phase2_download_stats.json"
    log_file = "download_error_log.txt"
    img_dir = "data/images"
    
    run_downloader(input_file, output_file, stats_file, log_file, img_dir)
