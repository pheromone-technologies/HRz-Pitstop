import json
import os
import shutil
import re

def is_accessory(p):
    cat = (p.get('category') or '').strip()
    sub = (p.get('subcategory') or '').strip().lower()
    name = (p.get('name') or '').strip()
    nl = name.lower()
    price = float(p.get('price') or 0)

    # 1. HELMETS
    if cat == 'Helmets':
        if sub == 'helmet accessories':
            return True
        acc_tokens = [
            'insert', 'pinlock', 'protector', 'film', 'screen guard', 'tear off', 'tear-off',
            'anti fog', 'anti-fog', 'antifog', 'cleaner', 'spray', 'foam', 'chin mount',
            'chinmount', 'chin strap', 'mobile holder', 'helmet lock', 'cable lock',
            'fitting', 'pivot kit', 'ratchet', 'mechanism', 'base plate', 'cheek pad',
            'breath deflector', 'chin curtain', 'bluetooth', 'intercom', 'headset',
            'outer visor', 'dark smoke visor', 'mirror visor', 'metal visor', 'short visor',
            'aluminium visor', 'full face visor', 'visor helios', 'visor protection',
            'interior cleaner', 'visor clean'
        ]
        if any(tok in nl for tok in acc_tokens):
            return True
        if 'visor' in nl and any(b in nl for b in ['mt 15', 'hunter', 'guerrilla', 'apache', 'triumph', 'yamaha', 'xsr', 'hness', 'cb200x', 'xpulse']):
            return True
        if nl.startswith('axor helmets spoiler') or ('spoiler' in nl and price < 1500 and not any(m in nl for m in ['thunder', 'fighter', 'typhoon', 'raider', 'sbh', 'ff', 'f/f', 'apex'])):
            return True
        if re.search(r'\bhelmet strap\b', nl) or (re.search(r'\bstrap\b', nl) and price < 500):
            return True
        if sub == 'visors & spoilers':
            is_full_helmet = any(m in nl for m in ['typhoon', 'fighter', 'thunder', 'sbh', 'stellar', 'raider', 'jet', 'cruiser', 'x cross']) and price >= 900
            if not is_full_helmet:
                return True
        return False

    # 2. RIDING JACKETS & APPAREL
    if cat == 'Riding Jackets & Apparel':
        if sub in ['arm sleeves', 'socks', 'headwear', 'headwear & balaclavas', 'base layers']:
            return True
        acc_tokens = ['sleeve', 'socks', 'balaclava', 'head cap', 'mask', 'armor', 'rain coat', 'rainwear', 'base layer', 'inner']
        if any(tok in nl for tok in acc_tokens) and not any(core in nl for core in ['jacket', 'suit', 'pant']):
            return True
        return False

    # 3. BOOTS & FOOTWEAR
    if cat == 'Boots & Footwear':
        if sub in ['boot rain covers']:
            return True
        if any(tok in nl for tok in ['gearboot', 'shoe cover', 'boot cover', 'shift protector', 'socks', 'slider']) and not any(core in nl for core in ['boot', 'shoe']):
            return True
        if 'gearboot' in nl or (price < 800 and 'cover' in nl):
            return True
        return False

    # 4. LUGGAGE & STORAGE
    if cat == 'Luggage & Storage':
        acc_tokens = ['bungeecord', 'bungee cord', 'bungee', 'bottle holder', 'rain cover', 'mounting strap']
        if any(tok in nl for tok in acc_tokens):
            return True
        return False

    # 5. LIGHTING & ELECTRICAL
    if cat == 'Lighting & Electrical':
        acc_tokens = ['clamp', 'mount set', 'foglight mount', 'fog light mount', 'mounting bracket', 'wire harness', 'harness', 'dimmer']
        if any(tok in nl for tok in acc_tokens) and not any(core in nl for core in ['foglight', 'fog lamp', 'headlight', 'bulb', 'light']):
            return True
        if 'clamp' in nl or 'mount set' in nl or 'foglight mount' in nl or 'fog light mount' in nl:
            return True
        return False

    # 6. CRASH PROTECTION
    if cat == 'Crash Protection':
        if any(k in nl for k in ['+bolts', '+ bolts', '& bolts', '&bolts', 'replacement puck', 'slider puck', 'spare bolt', 'bolt kit']):
            return True
        return False

    # 7. DRIVE & TRANSMISSION
    if cat == 'Drive & Transmission':
        acc_tokens = ['chain lub', 'chain lube', 'chain clean', 'chain paste', 'maintenance kit', 'care kit', 'brush', 'brite-o']
        if any(tok in nl for tok in acc_tokens):
            return True
        return False

    # 8. ELECTRONICS
    if cat == 'Electronics':
        acc_tokens = ['cable', 'clamp kit', 'mic sponge', 'replacement mount', 'spacer', 'charging cable', 'usb cable']
        if any(tok in nl for tok in acc_tokens) and not any(core in nl for core in ['intercom', 'bluetooth', 'charger', 'holder', 'mount pro', 'tracker']):
            return True
        return False

    return False

def main():
    src_path = 'data/products.json'
    bak_path = 'data/products.json.bak_tier'
    test_path = 'test design site/data/products.json'

    with open(src_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Backup original
    shutil.copy2(src_path, bak_path)
    print(f"Backed up {src_path} -> {bak_path}")

    # Group by category, maintaining category encounter order
    by_category = {}
    category_order = []
    for p in products:
        c = p.get('category', 'Unknown')
        if c not in by_category:
            by_category[c] = []
            category_order.append(c)
        by_category[c].append(p)

    reordered = []
    stats = {}
    for c in category_order:
        items = by_category[c]
        core = [p for p in items if not is_accessory(p)]
        acc = [p for p in items if is_accessory(p)]
        reordered.extend(core + acc)
        stats[c] = {'total': len(items), 'core': len(core), 'acc': len(acc)}

    assert len(reordered) == len(products), f"Length mismatch: {len(reordered)} vs {len(products)}"
    orig_ids = set(p['id'] for p in products)
    new_ids = set(p['id'] for p in reordered)
    assert orig_ids == new_ids, "Set of product IDs changed!"

    # Save to data/products.json
    with open(src_path, 'w', encoding='utf-8') as f:
        json.dump(reordered, f, indent=2, ensure_ascii=False)
    print(f"Updated {src_path} ({len(reordered)} products)")

    # Save to test design site/data/products.json
    if os.path.exists('test design site/data'):
        with open(test_path, 'w', encoding='utf-8') as f:
            json.dump(reordered, f, indent=2, ensure_ascii=False)
        print(f"Updated {test_path} ({len(reordered)} products)")

    # Print summary for Helmets and other key categories
    for cat in ['Helmets', 'Riding Jackets & Apparel', 'Luggage & Storage', 'Crash Protection', 'Lighting & Electrical', 'Drive & Transmission', 'Boots & Footwear']:
        if cat in stats:
            s = stats[cat]
            print(f"  {cat}: {s['core']} core first, {s['acc']} accessories last (Total: {s['total']})")

    # Sample top 8 helmets
    helmets = [p for p in reordered if p.get('category') == 'Helmets']
    print("\nTop 8 Helmets in catalog:")
    for i, p in enumerate(helmets[:8]):
        print(f"  {i+1}. {p.get('name')} (Rs.{p.get('price')})")

if __name__ == '__main__':
    main()
