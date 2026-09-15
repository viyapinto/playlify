import requests
import os
import io
from PIL import Image

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = "http://localhost:8000/predict"

primary_path = os.path.join(ROOT_DIR, "data", "images", "0.jpg")
fallback_path = os.path.join(ROOT_DIR, "frontend", "public", "examples", "example_1.jpg")
IMAGE_PATH = primary_path if os.path.exists(primary_path) else fallback_path

def run_tests():
    print("--- Starting API Tests ---")
    
    # Test 1: Valid Image
    print("\n[Test 1] Valid Image Prediction")
    if os.path.exists(IMAGE_PATH):
        with open(IMAGE_PATH, "rb") as f:
            files = {"image": ("0.jpg", f, "image/jpeg")}
            data = {"k": 5}
            response = requests.post(API_URL, files=files, data=data)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Prediction successful.")
                result = response.json()
                print(f"Predicted Genre: {result['prediction']['genre']}")
                print(f"Confidence: {result['prediction']['confidence']:.2f}")
                print(f"Similar Albums Found: {len(result['similar_albums'])}")
            else:
                print(f"Failed: {response.text}")
    else:
        print(f"Skipped: Image not found at {IMAGE_PATH}")

    # Test 2: Invalid File Type (Text file)
    print("\n[Test 2] Invalid File Type (Text)")
    files = {"image": ("test.txt", io.BytesIO(b"this is a text file, not an image"), "text/plain")}
    response = requests.post(API_URL, files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 400:
        print("Success: API correctly rejected the text file.")

    # Test 3: Missing File
    print("\n[Test 3] Missing File")
    response = requests.post(API_URL)
    print(f"Status: {response.status_code}")
    if response.status_code == 422:
        print("Success: API correctly rejected request without file.")

    # Test 4: Corrupted Image
    print("\n[Test 4] Corrupted Image")
    files = {"image": ("corrupt.jpg", io.BytesIO(b"corrupted image bytes 123456"), "image/jpeg")}
    response = requests.post(API_URL, files=files)
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        print(f"Success: API correctly handled corrupted image. Response: {response.text}")
    else:
        print(f"Unexpected response: {response.text}")

    print("\n--- API Tests Complete ---")

if __name__ == "__main__":
    try:
        requests.get("http://localhost:8000/health")
    except requests.exceptions.ConnectionError:
        print("ERROR: Backend server is not running on localhost:8000")
    else:
        run_tests()
