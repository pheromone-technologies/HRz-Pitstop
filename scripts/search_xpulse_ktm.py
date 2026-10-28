import urllib.request
import urllib.parse
import json

headers = {'User-Agent': 'Mozilla/5.0'}

queries = [
    'x pulse defender crash guard',
    'x pulse radiator grill',
    'x pulse tricorn',
    'ktm adv 390 raptor crash',
    'ktm adv 390 2025 radiator grill',
    'ktm adv 390 2025 bashplate',
    'ktm adv 390 2025 headlight grill',
    'ktm adv 390 2025 saddle stay',
    'ktm adv 390 2025 gps mount',
    'ktm adv 390 2025 carrier'
]

for q in queries:
    url = f"https://www.legundary.com/search/suggest.json?q={urllib.parse.quote(q)}&resources[type]=product"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            prods = data.get('resources', {}).get('results', {}).get('products', [])
            print(f"\nQuery '{q}': {len(prods)} products")
            for p in prods[:3]:
                print(f"  {p.get('title')} | {p.get('handle')}")
                print(f"    {p.get('image')}")
    except Exception as e:
        print(f"Error {q}: {e}")
