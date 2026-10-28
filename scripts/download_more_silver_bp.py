import urllib.request
import os
from PIL import Image

headers = {'User-Agent': 'Mozilla/5.0'}
urls = [
    'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_9fd8285b-bd14-47ea-b11c-0799fba9c94e.jpg?v=1770967774',
    'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2_6fdfecde-bb65-4baa-880a-4fd44d342d22.jpg?v=1770967774',
    'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/3_9102d687-bb4a-48dd-b5bf-0a6c9f43b977.jpg?v=1770967774',
    'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/4_68b7fee5-2f47-4dec-aaff-68f5b0b9082c.jpg?v=1770967774',
]

for i, url in enumerate(urls):
    dest = f"scratch/image_candidates/silver_bp_{i+2}.jpg"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp, open(dest, 'wb') as f:
        f.write(resp.read())
    im = Image.open(dest)
    print(f"Downloaded silver_bp_{i+2}: size={im.size}")
