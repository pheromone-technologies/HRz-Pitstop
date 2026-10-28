import json
import os
import re

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

with open('tools/output/verified_images_checkpoint.json', 'r', encoding='utf-8') as f:
    ckpt = json.load(f)

ckpt_by_name = { (v.get('product_name') or '').strip().lower(): v for v in ckpt.values() }

crash_prods = [p for p in products if (p.get('category') or '').lower() == 'crash protection']

print(f"Total Crash Protection products: {len(crash_prods)}")

has_source = 0
source_types = {}

for p in crash_prods:
    name = p['name'].strip().lower()
    entry = ckpt_by_name.get(name)
    if entry and entry.get('source'):
        has_source += 1
        stype = entry['source'].split(':')[0]
        source_types[stype] = source_types.get(stype, 0) + 1

print(f"Crash protection products with known source: {has_source}/{len(crash_prods)}")
print(f"Source types: {source_types}")
