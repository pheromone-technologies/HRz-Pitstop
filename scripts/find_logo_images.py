import json
import os

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

logo_prods = []
for p in products:
    img = (p.get('image') or '').lower()
    name = (p.get('name') or '').lower()
    brand = (p.get('brand') or '').lower()
    gal = [g.lower() for g in p.get('gallery', [])]
    
    is_logo = (
        'logo' in img 
        or 'warrior' in img 
        or 'autologue' in img 
        or 'brand' in img
        or any('logo' in g or 'warrior' in g or 'autologue' in g for g in gal)
        or 'auto warrior' in brand
        or 'autowarrior' in brand
    )
    if is_logo:
        logo_prods.append(p)

print(f"Total products matched with logo keywords: {len(logo_prods)}")
for p in logo_prods:
    print(f"  ID: {p['id']} | Name: {p['name']} | Brand: {p.get('brand')} | Img: {p.get('image')}")
