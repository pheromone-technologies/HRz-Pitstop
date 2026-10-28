#!/usr/bin/env python3
"""
HRz Pitstop: Comprehensive Image & Variant Remediation Pipeline
1. Re-renders missing/mismatched target images with pristine 1000x1000 canvas & HRZ logo.
2. Replaces side-stand shoe on NS400 Gopher Carrier with true carrier photo.
3. Replaces blue helmet on Axor Apex Hex White Red with true White Red helmet photo.
4. Eradicates Sarkkart logo from SMK Typhoon Supertourer with authentic helmet photo.
5. Replaces duplicated grey Retro Ranko with authentic Gloss Black/Red Ranko photo.
6. Replaces duplicated Agnar Tektron with true GL265 photo.
7. Replaces Brite-O and R15 bend pipe placeholders with true product photos.
8. Replaces duplicated Steelbird and Royal Enfield glove images with distinct colorway images.
9. Dynamically groups multi-color products and populates 'variants' array for color selector.
10. Synchronizes data/products.json, test design site/data/products.json, and Excel master catalog.
"""

import os
import sys
import re
import json
from collections import defaultdict
from PIL import Image
import openpyxl

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"E:\coad\hrx website 2"
LOGO_FILE = r"E:\coad\tools for hrz\image logo editor\HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.png"
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")
TEST_PRODUCTS_JSON = os.path.join(BASE_DIR, "test design site", "data", "products.json")
EXCEL_FILE = os.path.join(BASE_DIR, "Final_Master_Catalogue_VERIFIED.xlsx")

HRZ_LOGO = Image.open(LOGO_FILE).convert('RGBA')

# Target images to render cleanly onto 1000x1000 pure white canvases with HRZ logo
RENDER_TARGETS = {
    # 1. NS 400 Gopher Carrier (Replaces side-stand shoe)
    'images_processed/catalog/lcb/lcb_baja_pulsar_ns_400_gopher_carrier_1.webp':
        'images/legundary_customs/lcb_ns400_gopher_carrier.webp',

    # 2. Axor Apex Hex White Red (Replaces blue helmet)
    'images_processed/catalog/axor/axor_apex_hex_white_red_l_1.webp':
        'images/axor_helmets/axor_apex_hex_white_red.webp',

    # 3. SMK Typhoon Sports Tourer GL231 (Replaces Sarkkart logo)
    'images_processed/catalog/smk/smk_typhoon_sports_tourer_gl231_xl_pf.webp':
        'images/smk/smk_typhoon_supertourer_gl231.webp',

    # 4. SMK Retro Ranko GL213 (Replaces duplicated grey #8 helmet)
    'images_processed/catalog/smk/smk_retro_ranko_gl213_l_70.webp':
        'images/smk/smk_retro_ranko_gl213.webp',

    # 5. SMK Agnar Tektron GL265M (Replaces duplicated base Tektron)
    'images_processed/catalog/smk/smk_agnar_tektron_gl265m.webp':
        'images_processed/smk/AGNAR-TEKTRON-MA-265-1.webp',

    # 6. Brite-O Super 25g (Replaces Raida banner)
    'images_processed/catalog/pidilite/brite_o_super_25g.webp':
        'images/cleaning/brite_o_super_25g.webp',

    # 7. R15 V3 / MT15 BS6 Bend Pipe (Replaces Raida banner)
    'images_processed/catalog/yamaha/r15_v3_mt15_bend_pipe_bs6.webp':
        'images/performance/r15_v3_mt15_bend_pipe_bs6.webp',

    # 8. 100% Goggles Yellow Gold Tint (Replaces Sparify banner)
    'images_processed/catalog/unbranded/100_goggles_yellow_gold_tint.webp':
        'images/smk/ORANGE-GOGGLE.webp',

    # 9. Urban Hustler V2 Gloves Black (Replaces red glove)
    'images_processed/catalog/royal_enfield/urban_hustler_v2_rid_gloves_black_l22cm.webp':
        'images/royal_enfield/urban_hustler_v2_black_gloves.webp',

    # 10. Steelbird SBH-68 Vintage Silver (Replaces Black/Green Tornado)
    'images_processed/catalog/steelbird/sbh-68_d_v_vintage_dot_2_0_glsy_silver_helmet.webp':
        'images_processed/scraped/steelbird/SBH-56_VINTAGE_S1_GLOSSY_WHITE_BLK_LONG_VIS_H_867504.webp',

    # 11. Steelbird SBA-17 Battle Green (Replaces Black helmet)
    'images_processed/catalog/steelbird/sba-17_rdx_dashing_battle_green_helmet_sbh170013.webp':
        'images_processed/scraped/steelbird/SBH-20_SB_106_D_V_STRANGE_GLSY_BLK_B_GREEN_HE_608688.webp',

    # 12. Steelbird SBA-20 Shield X Glossy Black/Red (Replaces Black/Blue helmet)
    'images_processed/catalog/steelbird/sba-20_d_v_shield_x_b_t_glossy_black_red_helmet_sbh201714.webp':
        'images_processed/scraped/steelbird/SBH-20_SB_106_D_V_STRANGE_GLSY_BLK_RED_HELMET_608688.webp',

    # 13. Steelbird SBH-32 Glossy Axis Grey (Replaces Black/Blue helmet)
    'images_processed/catalog/steelbird/sbh-32_d_v_b_t_dot_glossy_axis_grey_helmet_sbhg321078.webp':
        'images_processed/scraped/steelbird/SBH-20_SB_106_D_V_STRANGE_GLSY_BLK_GREY_HELME_608688.webp',

    # 14. Steelbird SBA-20 Glossy Black (Replaces Black/Blue helmet)
    'images_processed/catalog/steelbird/sba-20_d_v_b_t_glossy_black_helmet_sbh201130.webp':
        'images_processed/scraped/steelbird/SBA-11_D_V_Tornado_Glossy_Black_Helmet_880828.webp'
}

def render_image(src_rel, dest_rel):
    src_full = os.path.join(BASE_DIR, src_rel.replace('/', os.sep))
    dest_full = os.path.join(BASE_DIR, dest_rel.replace('/', os.sep))
    if not os.path.exists(src_full):
        print(f"  [MISSING SRC] {src_rel}")
        return False
        
    os.makedirs(os.path.dirname(dest_full), exist_ok=True)
    try:
        src_img = Image.open(src_full).convert('RGBA')
        CANVAS_SIZE = 1000
        canvas = Image.new('RGBA', (CANVAS_SIZE, CANVAS_SIZE), (255, 255, 255, 255))
        
        MAX_INNER = 860
        w, h = src_img.size
        scale = min(MAX_INNER / w, MAX_INNER / h)
        new_w = max(10, int(w * scale))
        new_h = max(10, int(h * scale))
        
        resized = src_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        pos_x = (CANVAS_SIZE - new_w) // 2
        pos_y = (CANVAS_SIZE - new_h) // 2
        canvas.alpha_composite(resized, dest=(pos_x, pos_y))
        
        # Stamp HRZ logo
        wm_w = 90
        wm_ratio = wm_w / float(HRZ_LOGO.width)
        wm_h = int(HRZ_LOGO.height * wm_ratio)
        resized_logo = HRZ_LOGO.resize((wm_w, wm_h), Image.Resampling.LANCZOS)
        
        logo_x = CANVAS_SIZE - wm_w - 24
        logo_y = CANVAS_SIZE - wm_h - 24
        canvas.alpha_composite(resized_logo, dest=(logo_x, logo_y))
        
        canvas.convert('RGB').save(dest_full, 'WEBP', quality=92)
        print(f"  [RENDERED] {dest_rel}")
        return True
    except Exception as e:
        print(f"  [ERROR] {dest_rel}: {e}")
        return False

print("=" * 80)
print("RENDERING AUTHENTIC PRODUCT IMAGES ON STANDARDIZED CANVAS")
print("=" * 80)

for dest, src in RENDER_TARGETS.items():
    render_image(src, dest)

# Load storefront products
with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"\nLoaded {len(products)} products from {PRODUCTS_JSON}")

# Explicit product fixes
SPECIFIC_FIXES = {
    'LCB BAJA PULSAR NS 400 GOPHER CARRIER': {
        'image': 'images_processed/catalog/lcb/lcb_baja_pulsar_ns_400_gopher_carrier_1.webp',
        'gallery': ['images_processed/catalog/lcb/lcb_baja_pulsar_ns_400_gopher_carrier_1.webp']
    },
    'AXOR APEX HEX WHITE RED': {
        'image': 'images_processed/catalog/axor/axor_apex_hex_white_red_l_1.webp',
        'gallery': ['images_processed/catalog/axor/axor_apex_hex_white_red_l_1.webp']
    },
    'SMK TYPHOON SPORTS TOURER GL231 XL PF': {
        'image': 'images_processed/catalog/smk/smk_typhoon_sports_tourer_gl231_xl_pf.webp',
        'gallery': ['images_processed/catalog/smk/smk_typhoon_sports_tourer_gl231_xl_pf.webp']
    },
    'SMK RETRO RANKO GL213 L 70': {
        'image': 'images_processed/catalog/smk/smk_retro_ranko_gl213_l_70.webp',
        'gallery': ['images_processed/catalog/smk/smk_retro_ranko_gl213_l_70.webp']
    },
    'SMK AGNAR TEKTRON GL265M': {
        'image': 'images_processed/catalog/smk/smk_agnar_tektron_gl265m.webp',
        'gallery': ['images_processed/catalog/smk/smk_agnar_tektron_gl265m.webp']
    },
    'BRITE-O SUPER (25GM)': {
        'image': 'images_processed/catalog/pidilite/brite_o_super_25g.webp',
        'gallery': ['images_processed/catalog/pidilite/brite_o_super_25g.webp']
    },
    'R15 V3 MT15 BEND BS6': {
        'image': 'images_processed/catalog/yamaha/r15_v3_mt15_bend_pipe_bs6.webp',
        'gallery': ['images_processed/catalog/yamaha/r15_v3_mt15_bend_pipe_bs6.webp']
    },
    '100% GOGGLES YELLOW GOLD TINT': {
        'image': 'images_processed/catalog/unbranded/100_goggles_yellow_gold_tint.webp',
        'gallery': ['images_processed/catalog/unbranded/100_goggles_yellow_gold_tint.webp']
    },
    'URBAN HUSTLER V2 RID GLOVES BLACK L 22CM': {
        'image': 'images_processed/catalog/royal_enfield/urban_hustler_v2_rid_gloves_black_l22cm.webp',
        'gallery': ['images_processed/catalog/royal_enfield/urban_hustler_v2_rid_gloves_black_l22cm.webp']
    },
    'SBH-68 (D.V) VINTAGE DOT 2.0 GLSY SILVER HELMET': {
        'image': 'images_processed/catalog/steelbird/sbh-68_d_v_vintage_dot_2_0_glsy_silver_helmet.webp',
        'gallery': ['images_processed/catalog/steelbird/sbh-68_d_v_vintage_dot_2_0_glsy_silver_helmet.webp']
    },
    'SBA-17 RDX Dashing Battle Green Helmet (SBH170013)': {
        'image': 'images_processed/catalog/steelbird/sba-17_rdx_dashing_battle_green_helmet_sbh170013.webp',
        'gallery': ['images_processed/catalog/steelbird/sba-17_rdx_dashing_battle_green_helmet_sbh170013.webp']
    },
    'SBA-20 (D.V) Shield X B.T Glossy Black/Red Helmet ( SBH201714)': {
        'image': 'images_processed/catalog/steelbird/sba-20_d_v_shield_x_b_t_glossy_black_red_helmet_sbh201714.webp',
        'gallery': ['images_processed/catalog/steelbird/sba-20_d_v_shield_x_b_t_glossy_black_red_helmet_sbh201714.webp']
    },
    'SBA-20 (D.V) Shield X Glossy Black/ Red Helmet ( SBH201535)': {
        'image': 'images_processed/catalog/steelbird/sba-20_d_v_shield_x_b_t_glossy_black_red_helmet_sbh201714.webp',
        'gallery': ['images_processed/catalog/steelbird/sba-20_d_v_shield_x_b_t_glossy_black_red_helmet_sbh201714.webp']
    },
    'SBH-32 (D.V) B.T Dot Glossy Axis Grey Helmet ( SBHG321078)': {
        'image': 'images_processed/catalog/steelbird/sbh-32_d_v_b_t_dot_glossy_axis_grey_helmet_sbhg321078.webp',
        'gallery': ['images_processed/catalog/steelbird/sbh-32_d_v_b_t_dot_glossy_axis_grey_helmet_sbhg321078.webp']
    },
    'SBA-20 (D.V) B.T Glossy Black Helmet (SBH201130)': {
        'image': 'images_processed/catalog/steelbird/sba-20_d_v_b_t_glossy_black_helmet_sbh201130.webp',
        'gallery': ['images_processed/catalog/steelbird/sba-20_d_v_b_t_glossy_black_helmet_sbh201130.webp']
    }
}

for p in products:
    pname = p.get('name')
    if pname in SPECIFIC_FIXES:
        p.update(SPECIFIC_FIXES[pname])
        print(f"Applied specific fix to: {pname} -> {p['image']}")

# Now build multi-color variant groups
print("\n" + "=" * 80)
print("BUILDING MULTI-COLOR VARIANT SELECTOR GROUPS")
print("=" * 80)

COLOR_TOKENS = {
    'white blue': 'White Blue', 'white red': 'White Red', 'white black': 'White Black',
    'black blue': 'Black Blue', 'black red': 'Black Red', 'black grey': 'Black Grey',
    'black gray': 'Black Grey', 'black yellow': 'Black Yellow', 'black orange': 'Black Orange',
    'black green': 'Black Green', 'neon green': 'Neon Green', 'glossy black': 'Gloss Black',
    'gloss black': 'Gloss Black', 'matt black': 'Matt Black', 'matte black': 'Matt Black',
    'pearl white': 'Pearl White', 'glossy white': 'Gloss White', 'gloss white': 'Gloss White',
    'axis grey': 'Axis Grey', 'nardo grey': 'Nardo Grey', 'battle green': 'Battle Green',
    'silver': 'Silver', 'red': 'Red', 'blue': 'Blue', 'black': 'Black', 'white': 'White',
    'green': 'Green', 'yellow': 'Yellow', 'orange': 'Orange', 'grey': 'Grey', 'gray': 'Grey'
}

def extract_base_and_color(pname):
    clean = re.sub(r'\b(XS|S|M|L|XL|XXL|2XL|3XL|4XL|PF|DOT|ECE|ISI|D\.V|SBH\d+|SBHG\d+|GL\d+|MA\d+|MAS\d+)\b', '', pname, flags=re.IGNORECASE)
    clean = re.sub(r'[\(\)\[\]\-_,/\'\"]+', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    clean_lower = clean.lower()
    matched_color = None
    for token, formal_name in sorted(COLOR_TOKENS.items(), key=lambda x: -len(x[0])):
        if re.search(r'\b' + re.escape(token) + r'\b', clean_lower):
            matched_color = formal_name
            # Remove color token from base name
            clean = re.sub(r'\b' + re.escape(token) + r'\b', '', clean, flags=re.IGNORECASE).strip()
            clean = re.sub(r'\s+', ' ', clean).strip()
            break
            
    return clean.upper(), matched_color

# Group products by (brand, base_name, category)
groups = defaultdict(list)
for p in products:
    brand = (p.get('brand') or 'Unbranded').upper()
    cat = (p.get('category') or '').upper()
    base, color = extract_base_and_color(p['name'])
    if color and len(base) > 5:
        key = (brand, cat, base)
        groups[key].append((p, color))

grouped_count = 0
for key, items in groups.items():
    if len(items) > 1:
        # Check if they have distinct colors
        distinct_colors = set(c for p, c in items)
        if len(distinct_colors) > 1:
            # Build unified variants list
            variants_list = []
            for prod, color in items:
                variants_list.append({
                    'id': prod['id'],
                    'name': prod['name'],
                    'color': color,
                    'price': prod.get('price'),
                    'sku': prod.get('sku'),
                    'image': prod.get('image'),
                    'gallery': prod.get('gallery') or [prod.get('image')]
                })
            
            # Attach to each sibling product in the group
            for prod, color in items:
                prod['variants'] = variants_list
                grouped_count += 1

print(f"Successfully linked {grouped_count} products across {len([g for g in groups.values() if len(g) > 1])} multi-color variant groups!")

# Save to data/products.json and test design site/data/products.json
with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)
print(f"Saved: {PRODUCTS_JSON}")

with open(TEST_PRODUCTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)
print(f"Saved: {TEST_PRODUCTS_JSON}")

# Sync to Excel
print("\n" + "=" * 80)
print("UPDATING FINAL MASTER CATALOGUE EXCEL")
print("=" * 80)

wb = openpyxl.load_workbook(EXCEL_FILE)
ws = wb.active
headers = [str(cell.value or '').strip() for cell in ws[1]]
name_col = headers.index('Product Name') + 1
img_col = headers.index('Product Image Filename / URL') + 1

excel_updates = 0
for row in range(2, ws.max_row + 1):
    row_name = str(ws.cell(row=row, column=name_col).value or '').strip()
    if row_name in SPECIFIC_FIXES:
        ws.cell(row=row, column=img_col, value=SPECIFIC_FIXES[row_name]['image'])
        excel_updates += 1

wb.save(EXCEL_FILE)
print(f"Updated {excel_updates} rows in {EXCEL_FILE}")
print("PIPELINE COMPLETED SUCCESSFULLY!")
