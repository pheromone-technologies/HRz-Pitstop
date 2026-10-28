import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/products.json', encoding='utf-8') as f:
    products = json.load(f)

for p in products:
    name = p['name'].lower()
    if 'throttle' in name or 'grip' in name:
        print(p['id'], "|", p['name'][:40], "| cat:", p.get('category'), "| subcat:", p.get('subcategory'))
