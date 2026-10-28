import json

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

for idx, p in enumerate(products):
    if p.get('id') == 'hrz-carbonado-turtle-black-hard-shell-thigh-bag-5-litr-0446':
        print(f"Found Turtle at idx {idx}")
        for j in range(max(0, idx - 4), min(len(products), idx + 10)):
            item = products[j]
            print(f"[{j}] {item['id']} | {item['name']} | Rs.{item.get('price')} | {item.get('category')} | {item.get('image')}")
