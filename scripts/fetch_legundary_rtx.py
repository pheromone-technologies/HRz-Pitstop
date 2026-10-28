import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://www.legundary.com/collections/tvs-apache-rtx-300/products.json?limit=250'

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        products = data.get('products', [])
        print(f"Found {len(products)} products in collection:")
        for p in products:
            print(f"\nTitle: {p.get('title')}")
            print(f"Handle: {p.get('handle')}")
            images = [img.get('src') for img in p.get('images', [])]
            print(f"Images count: {len(images)}")
            for i, src in enumerate(images[:3]):
                print(f"  [{i+1}] {src}")
except Exception as e:
    print(f"Error fetching collection: {e}")
