import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print("--- Products around 1430 to 1475 ---")
for p in products:
    pid = p.get('id', '')
    if any(f'14{n}' in pid for n in range(30, 75)):
        print(f"{p.get('id')} | {p.get('category')} | {p.get('name')} | {p.get('image')}")
