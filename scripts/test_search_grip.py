import json

products = json.load(open('data/products.json', encoding='utf-8'))
STOP_WORDS = {'and', 'or', 'the', 'for', 'with', 'in', 'of', 'to', 'a', 'an', 'at', 'by', 'from', 'on', 'all', '&'}

def search(query):
    raw_tokens = [t.lower() for t in query.replace('&', ' ').split() if t]
    tokens = [t for t in raw_tokens if len(t) > 1 and t not in STOP_WORDS]
    if not tokens:
        tokens = [t for t in raw_tokens if t]
    
    results = []
    for p in products:
        name = p['name'].lower()
        cat = p.get('category', '').lower()
        subcat = p.get('subcategory', '').lower()
        brand = p.get('brand', '').lower()
        
        name_words = name.split()
        
        score = 0
        matched_tokens = 0
        
        for t in tokens:
            root = t[:-1] if t.endswith('s') and len(t) > 3 else t
            t_score = 0
            
            # 1. Exact or root word match in name (highest relevance)
            for w in name_words:
                w_clean = ''.join(c for c in w if c.isalnum())
                if w_clean == t or w_clean == root:
                    t_score = max(t_score, 40)
                    break
                elif w_clean.startswith(root) or w_clean.startswith(t):
                    t_score = max(t_score, 25)
                    break
            
            # 2. Subcategory or Category match
            if t_score == 0:
                for w in set(subcat.split() + cat.split()):
                    w_clean = ''.join(c for c in w if c.isalnum())
                    if w_clean == t or w_clean == root:
                        t_score = max(t_score, 20)
                        break
            
            # 3. Substring match only if token >= 4 chars and within word
            if t_score == 0 and len(t) >= 4:
                if any(t in w for w in name_words):
                    t_score = max(t_score, 15)
            
            if t_score > 0:
                matched_tokens += 1
                score += t_score
        
        if matched_tokens > 0:
            if matched_tokens == len(tokens):
                score *= 2.0
            else:
                score *= (matched_tokens / len(tokens))
            results.append((p, score))
    
    results.sort(key=lambda x: -x[1])
    return results

res = search('Grips and Throttle')
print(f"Results count: {len(res)}")
for p, s in res:
    print(f"[{s:.1f}] {p['name']} | Cat: {p['category']} | Sub: {p.get('subcategory')}")
