import json

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

for idx, p in enumerate(products):
    if 'quench' in p.get('name', '').lower():
        print(f"Found at index {idx}:")
        print(json.dumps(p, indent=2))
        print("\nSurrounding products (idx-3 to idx+6):")
        for s in products[max(0, idx-3):min(len(products), idx+7)]:
            print(f"  [{s['id']}] {s['name']} | Rs.{s.get('price')} | {s.get('image')}")
