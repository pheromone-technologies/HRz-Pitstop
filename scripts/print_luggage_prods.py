import json

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

luggage_prods = [p for p in products if 'Luggage' in p.get('category', '')]
print(f"Total Luggage products: {len(luggage_prods)}")

for p in luggage_prods:
    print(f"{p['id']} | {p['name']} | Rs.{p.get('price')} | {p.get('image')}")
