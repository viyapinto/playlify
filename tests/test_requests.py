import os
import requests, time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
example_img_path = os.path.join(ROOT_DIR, 'frontend', 'public', 'examples', 'example_1.jpg')

url = 'http://localhost:8000/predict'
try:
    with open(example_img_path, 'rb') as f:
        img_data = f.read()
except:
    print('Cannot find example image, exiting')
    exit(1)

for i in range(10):
    start = time.time()
    try:
        res = requests.post(url, files={'image': ('example_1.jpg', img_data, 'image/jpeg')}, data={'k': 10})
        print(f'Request {i+1}: status={res.status_code}, time={time.time()-start:.2f}s')
    except Exception as e:
        print(f'Request {i+1} failed: {e}')
    time.sleep(0.5)
