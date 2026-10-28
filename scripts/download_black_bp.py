import urllib.request
import os

headers = {'User-Agent': 'Mozilla/5.0'}
urls = [
    'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1.jpg_2.jpg?v=1771827830',
    'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2.jpg_2.jpg?v=1771827830',
    'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/3_jpg.jpg?v=1771827821',
]

for i, url in enumerate(urls):
    dest = f"scratch/image_candidates/black_bp_{i+2}.jpg"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp, open(dest, 'wb') as f:
        f.write(resp.read())
    print(f"Downloaded black_bp_{i+2}")
