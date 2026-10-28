import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for query in ['apache rtx', 'rtx 300', 'rtx vambrace', 'rtx vector']:
    url = f"https://www.legundary.com/search/suggest.json?q={urllib.parse.quote(query)}&resources[type]=product"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            prods = data.get('resources', {}).get('results', {}).get('products', [])
            print(f"Query '{query}': found {len(prods)} products")
            for p in prods:
                print(f"  Title: {p.get('title')} | Handle: {p.get('handle')} | Img: {p.get('image')}")
    except Exception as e:
        print(f"Error for '{query}': {e}")
