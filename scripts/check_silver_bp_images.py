import urllib.request
import json

headers = {'User-Agent': 'Mozilla/5.0'}
url = "https://www.legundary.com/products/tvs-apache-rtx-300-vambrace-bashplate-silver.json"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    images = data.get('product', {}).get('images', [])
    for i, img in enumerate(images):
        print(f"[{i+1}] {img['src']}")
