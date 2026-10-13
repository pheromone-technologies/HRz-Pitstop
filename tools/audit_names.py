import json
import csv
import re

PRODUCTS_FILE = 'data/products.json'
OUT_FILE = 'audit_names_review.csv'

with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
    products = json.load(f)

flagged = []

bad_words = ['price in india', 'buy online', 'helmet shop', 'for sale', 'cheap', 'discount', 'category:', 'riding gear']

for p in products:
    name = p['name']
    brand = p.get('brand', '')
    name_lower = name.lower()
    brand_lower = brand.lower()

    reasons = []

    if brand_lower and name_lower.count(brand_lower) >= 2 and len(brand_lower) > 2:
        reasons.append('brand twice')
        
    if len(name) > 80:
        reasons.append('unusually long (>80 chars)')
        
    for w in bad_words:
        if w in name_lower:
            reasons.append(f'contains "{w}"')
            
    words = [w for w in re.findall(r'\b\w+\b', name_lower) if len(w) > 3]
    for w in set(words):
        if words.count(w) >= 3: 
            reasons.append(f'repeated word: {w}')

    if reasons:
        flagged.append({
            'name': name,
            'sku': p.get('sku', ''),
            'brand': brand,
            'category': p.get('category', ''),
            'reasons': ' | '.join(reasons)
        })

with open(OUT_FILE, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['name', 'sku', 'brand', 'category', 'reasons'])
    writer.writeheader()
    writer.writerows(flagged)

print(f'Total flagged names: {len(flagged)}')
