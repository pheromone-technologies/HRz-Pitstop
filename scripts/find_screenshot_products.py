import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/products.json', encoding='utf-8') as f:
    products = json.load(f)

# Let's see what smartSearch would return for 'Grips and Throttle'
# tokens: 'grips', 'and', 'throttle'
tokens = ['grips', 'and', 'throttle']
matches = []

for p in products:
    name_low = p['name'].lower()
    cat_low = p.get('category', '').lower()
    sub_low = p.get('subcategory', '').lower()
    
    # Check if 'rcb replica handle grips' is in it
    if 'rcb replica' in name_low or 'quick throttle' in name_low:
        matches.append(p)

print(f"Total matching RCB/Throttle: {len(matches)}")
for p in matches[:10]:
    print(p['id'], "|", p['name'], "|", p.get('image'))
