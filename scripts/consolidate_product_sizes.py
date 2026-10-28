import json
import os
import shutil
import re

size_categories = [
    'Riding Jackets & Apparel', 'Helmets', 'Gloves', 'Riding Pants', 'Boots & Footwear'
]

STANDARD_SIZES = {
    'Riding Jackets & Apparel': ['S', 'M', 'L', 'XL', '2XL', '3XL'],
    'Helmets': ['S', 'M', 'L', 'XL', '2XL'],
    'Gloves': ['S', 'M', 'L', 'XL', '2XL'],
    'Riding Pants': ['30', '32', '34', '36', '38', '40'],
    'Boots & Footwear': ['UK 7', 'UK 8', 'UK 9', 'UK 10', 'UK 11', 'UK 12']
}

DEFAULT_AVAIL_SIZES = {
    'Riding Jackets & Apparel': ['M', 'L', 'XL'],
    'Helmets': ['M', 'L', 'XL'],
    'Gloves': ['M', 'L', 'XL'],
    'Riding Pants': ['32', '34', '36'],
    'Boots & Footwear': ['UK 8', 'UK 9', 'UK 10']
}

def normalize_size_token(s):
    s = s.strip().upper().replace(' ', '')
    if s == 'XXL': return '2XL'
    if s == 'XXXL': return '3XL'
    return s

def extract_size_and_clean_name(name, category):
    if category not in size_categories:
        return None, name

    raw_name = name.strip()

    # 1. Boots
    if category == 'Boots & Footwear':
        m_boot = re.search(r'\b(?:UK\s*|SIZE\s*)(\d{1,2})\b', raw_name, re.IGNORECASE)
        if m_boot:
            size = f"UK {m_boot.group(1)}"
            base = re.sub(r'\s*\b(?:UK\s*|SIZE\s*)\d{1,2}\b', '', raw_name, flags=re.IGNORECASE).strip()
            base = re.sub(r'\s*/\s*$', '', base).strip()
            return size, base
        m_num = re.search(r'\b(6|7|8|9|10|11|12|13)\s*$', raw_name)
        if m_num:
            size = f"UK {m_num.group(1)}"
            base = raw_name[:m_num.start()].strip()
            return size, base

    # 2. Pants
    if category == 'Riding Pants':
        m_pant = re.search(r'[/\s\(]+(2[89]|3[0-9]|4[0-4])[/\s\)]*$', raw_name)
        if m_pant:
            size = m_pant.group(1)
            base = raw_name[:m_pant.start()].strip()
            base = re.sub(r'\s+[SMLXL2345]{1,3}\s*$', '', base, flags=re.IGNORECASE).strip()
            return size, base

    # 3. Parentheses size: "AXE RACING BLACK-RED(L)", "LR 3LAYER PANT TROTTER WITH TAILBONE (2 XL)", "PROBIKER (M)"
    m_paren = re.search(r'[\(\[\{]\s*(XS|S|M|L|XL|2\s*XL|3\s*XL|4\s*XL|XXL|XXXL|\d{2})\s*[\)\]\}]', raw_name, re.IGNORECASE)
    if m_paren:
        size = normalize_size_token(m_paren.group(1))
        base = raw_name[:m_paren.start()].strip() + " " + raw_name[m_paren.end():].strip()
        base = re.sub(r'\s+', ' ', base).strip()
        return size, base

    # 4. End hyphen/slash size: "CRAMSTER BREEZER JACKET BLACK WHITE-L", "DSG RACE PRO JACKET -BK/GLD GP -M", "LR MEN'S JACKET ADDON PRO L2-BLACK-3XL"
    m_end_hyphen = re.search(r'[-/\s]+\b(XS|S|M|L|XL|2\s*XL|3\s*XL|4\s*XL|XXL|XXXL)\s*$', raw_name, re.IGNORECASE)
    if m_end_hyphen:
        size = normalize_size_token(m_end_hyphen.group(1))
        base = raw_name[:m_end_hyphen.start()].strip()
        base = re.sub(r'[-/\s]+$', '', base).strip()
        return size, base

    # 5. Slash pattern in middle: "ADDON PRO L2 JACKET MALE 3XL/ALL BLACK" -> 3XL
    m_slash = re.search(r'\b(XS|S|M|L|XL|2\s*XL|3\s*XL|4\s*XL|XXL|XXXL)\s*/\s*', raw_name, re.IGNORECASE)
    if m_slash:
        size = normalize_size_token(m_slash.group(1))
        base = raw_name[:m_slash.start()].strip() + " " + raw_name[m_slash.end():].strip()
        base = re.sub(r'\s+', ' ', base).strip()
        return size, base

    # 6. Size before color in middle: "ADDON PRO L2 JACKET MALE L BLACK/GRAY" -> size L
    color_lookahead = r'(?=\s+(?:BLACK|GRAY|GREY|NEON|RED|BLUE|WHITE|ORANGE|YELLOW|GREEN|HI-W|HI-V|ALL|BLK|GLD|GRY|RED-M|RED-L))'
    m_mid_color = re.search(r'(?<=\s)\b(XS|S|M|L|XL|2\s*XL|3\s*XL|4\s*XL|XXL|XXXL)\b' + color_lookahead, raw_name, re.IGNORECASE)
    if m_mid_color:
        size = normalize_size_token(m_mid_color.group(1))
        base = raw_name[:m_mid_color.start()].strip() + " " + raw_name[m_mid_color.end():].strip()
        base = re.sub(r'\s+', ' ', base).strip()
        return size, base

    # 7. Size after keyword "SIZE" or "SIZE-": "RAIDA - AVANTUR GLOVES RED SIZE-L"
    m_size_kw = re.search(r'\bSIZE\s*[-:]?\s*(XS|S|M|L|XL|2\s*XL|3\s*XL|4\s*XL|XXL|XXXL)\b', raw_name, re.IGNORECASE)
    if m_size_kw:
        size = normalize_size_token(m_size_kw.group(1))
        base = re.sub(r'\s*\bSIZE\s*[-:]?\s*(XS|S|M|L|XL|2\s*XL|3\s*XL|4\s*XL|XXL|XXXL)\b', '', raw_name, flags=re.IGNORECASE).strip()
        return size, base

    return None, name

def clean_canonical_name(name):
    cleaned = re.sub(r'^[A-Z0-9]+-[A-Z0-9_-]+\s+', '', name).strip()
    cleaned = re.sub(r'\s*-\s*$', '', cleaned).strip()
    return cleaned

def main():
    src_path = 'data/products.json'
    bak_path = 'data/products.json.bak_sizes'
    test_path = 'test design site/data/products.json'

    with open(src_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    shutil.copy2(src_path, bak_path)
    print(f"Backed up to {bak_path}")

    grouped_dict = {}
    order = []

    for p in products:
        cat = p.get('category', '')
        size, clean_name = extract_size_and_clean_name(p['name'], cat)

        if size and cat in size_categories:
            cname = clean_canonical_name(clean_name)
            norm_key = (cat, re.sub(r'[^a-z0-9]', '', cname.lower()))
            if norm_key not in grouped_dict:
                grouped_dict[norm_key] = {
                    'canonical': dict(p),
                    'clean_name': cname,
                    'variants': []
                }
                order.append(norm_key)

            grouped_dict[norm_key]['variants'].append({
                'size': size,
                'id': p['id'],
                'sku': p.get('sku', ''),
                'price': p.get('price', 0),
                'image': p.get('image', ''),
                'original_name': p['name'],
                'inStock': p.get('inStock', True)
            })
        else:
            unique_key = ('non_sized', p['id'])
            grouped_dict[unique_key] = {
                'canonical': dict(p),
                'clean_name': p['name'],
                'variants': []
            }
            order.append(unique_key)

    consolidated = []
    for k in order:
        entry = grouped_dict[k]
        p = entry['canonical']
        variants = entry['variants']
        cat = p.get('category', '')
        std = STANDARD_SIZES.get(cat, None)

        if variants:
            p['name'] = entry['clean_name']
            
            # Collect unique available sizes from in-stock variants
            avail_set = set()
            for v in variants:
                if v.get('inStock', True):
                    avail_set.add(v['size'])

            if not avail_set:
                avail_set = set(v['size'] for v in variants)

            avail = [s for s in std if s in avail_set] + [s for s in avail_set if s not in std]
            all_s = list(std) if std else list(avail)
            for s in avail:
                if s not in all_s:
                    all_s.append(s)

            # Dictionary of size variants keyed by size
            size_var_map = {}
            for v in variants:
                size_var_map[v['size']] = v

            p['availableSizes'] = avail
            p['allSizes'] = all_s
            p['sizes'] = ', '.join(avail)
            p['sizeVariants'] = size_var_map
        else:
            # If in size category, ensure availableSizes and allSizes exist
            if cat in size_categories and std:
                if p.get('sizes'):
                    parts = [s.strip().upper() for s in p['sizes'].split(',') if s.strip()]
                    p['availableSizes'] = parts
                    p['allSizes'] = list(dict.fromkeys(std + parts))
                else:
                    default_av = DEFAULT_AVAIL_SIZES.get(cat, std[:3])
                    p['availableSizes'] = default_av
                    p['allSizes'] = list(std)
                    p['sizes'] = ', '.join(default_av)
            elif p.get('sizes'):
                parts = [s.strip().upper() for s in p['sizes'].split(',') if s.strip()]
                p['availableSizes'] = parts
                p['allSizes'] = parts

        consolidated.append(p)

    print(f"Original products: {len(products)} -> Consolidated: {len(consolidated)}")

    with open(src_path, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    print(f"Saved {src_path}")

    if os.path.exists('test design site/data'):
        with open(test_path, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False)
        print(f"Saved {test_path}")

if __name__ == '__main__':
    main()
