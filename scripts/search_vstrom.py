import urllib.request
import urllib.parse
import json

headers = {'User-Agent': 'Mozilla/5.0'}
for q in ['v-strom', 'suzuki v strom', 'v strom 250', 'v strom sx', 'v strom 650']:
    url = f"https://www.legundary.com/search/suggest.json?q={urllib.parse.quote(q)}&resources[type]=product"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        prods = data.get('resources', {}).get('results', {}).get('products', [])
        print(f"\nQuery '{q}': {len(prods)} products")
        for p in prods:
            print(f"  {p.get('title')} | {p.get('handle')}")
            print(f"    {p.get('image')}")
