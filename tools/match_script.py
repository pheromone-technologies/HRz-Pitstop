import json
import pandas as pd
import re

# 1. Load Excel Items
df = pd.read_excel('StockSummaryReport_10_10_26.xlsx', header=2)
df = df.dropna(subset=['Item Name'])
excel_names = df['Item Name'].tolist()

# 2. Load JSON Site Items
with open('data/products.json', encoding='utf-8') as f:
    products = json.load(f)

site_names = [p['name'] for p in products]
site_brands = [p.get('brand', '') for p in products]

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())

clean_site_names = [clean_text(f"{brand} {name}") for brand, name in zip(site_brands, site_names)]
clean_site_names_no_brand = [clean_text(name) for name in site_names]

exact_matches = 0
partial_matches = 0
not_found = 0

matched_examples = []
not_found_examples = []

for raw_name in excel_names:
    cleaned = clean_text(raw_name)
    if not cleaned: continue
    
    # 1. Exact match
    if cleaned in clean_site_names or cleaned in clean_site_names_no_brand:
        exact_matches += 1
        continue
        
    # 2. Subset match
    tokens = set(cleaned.split())
    found_partial = False
    for site_clean in clean_site_names:
        site_tokens = set(site_clean.split())
        # If excel name tokens are largely in the site tokens
        if len(tokens) > 1 and len(tokens & site_tokens) / len(tokens) >= 0.8:
            partial_matches += 1
            found_partial = True
            if len(matched_examples) < 5:
                matched_examples.append(f"'{raw_name}' matched with site '{site_clean}'")
            break
            
    if not found_partial:
        not_found += 1
        if len(not_found_examples) < 5:
            not_found_examples.append(raw_name)

print(f"Total in Excel: {len(excel_names)}")
print(f"Exact Matches: {exact_matches}")
print(f"Partial/Fuzzy Matches: {partial_matches}")
print(f"Total Matched: {exact_matches + partial_matches}")
print(f"Not Found: {not_found}")
print("\nSample Matched:")
for m in matched_examples: print("-", m)
print("\nSample Not Found:")
for m in not_found_examples: print("-", m)
