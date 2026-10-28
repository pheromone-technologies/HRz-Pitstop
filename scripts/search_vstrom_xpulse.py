import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}

queries = ['v strom crash guard', 'v strom bashplate', 'v strom adrinex', 'v strom vambrace', 'x pulse headlight grill', 'x pulse cosmic']

for q in queries:
    url = f"https://www.legundary.com/search/suggest.json?q={urllib.parse.quote(q)}&resources[type]=product"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            prods = data.get('resources', {}).get('results', {}).get('products', [])
            print(f"\nQuery '{q}': {len(prods)} products found")
            for p in prods:
                print(f"  Title: {p.get('title')} | Handle: {p.get('handle')}")
                print(f"    Image: {p.get('image')}")
    except Exception as e:
        print(f"Error for '{q}': {e}")
