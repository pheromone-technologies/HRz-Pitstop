import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

for p in products:
    name = (p.get('name') or '').lower()
    pid = (p.get('id') or '').lower()
    if 'apache' in name:
        print(f"{pid:50s} | {p.get('name')}")
