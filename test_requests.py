import requests, time

url = 'http://localhost:8000/predict'
try:
    with open('frontend/public/examples/example_1.jpg', 'rb') as f:
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
