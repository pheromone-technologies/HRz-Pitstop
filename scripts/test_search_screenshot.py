import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/products.json', encoding='utf-8') as f:
    products = json.load(f)

# Replicate smartSearch in python
query = "Grips and Throttle"
tokens = [t for t in query.lower().split() if len(t) > 1] # ['grips', 'and', 'throttle']

scored = []
for p in products:
    nameStr = p['name'].lower()
    catStr = p.get('category', '').lower()
    subcatStr = p.get('subcategory', '').lower()
    brandStr = p.get('brand', '').lower()
    
    score = 0
    tokensMatched = 0
    for token in tokens:
        best = 0
        if token in nameStr: best = max(best, 10)
        if token in brandStr: best = max(best, 15)
        if token in catStr: best = max(best, 15)
        if token in subcatStr: best = max(best, 15)
        
        if best > 0:
            score += best
            tokensMatched += 1
            
    if tokensMatched > 0:
        if tokensMatched == len(tokens):
            score *= 2.0
        else:
            score *= (tokensMatched / len(tokens))
        scored.append((score, p))

scored.sort(key=lambda x: -x[0])
print(f"Total scored: {len(scored)}")
for s, p in scored[:10]:
    print(f"Score {s:5.1f} | {p['id']} | {p['name']} | image: {p.get('image')}")
