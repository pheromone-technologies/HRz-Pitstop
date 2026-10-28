import json
import os
import re
from image_standardizer import standardize_and_save

with open('data/products.json', encoding='utf-8') as f:
    products = json.load(f)

prod_map = {p['id']: p for p in products}

fixed = 0

# 1. SBH-68 JAZZ BLUE
sbh68 = prod_map.get('hrz-sbh-68-d-v-vintage-dot-2-0-glsy-jazz-blue-helmet-2642')
if sbh68:
    url = 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/steelbird_sbh_68_vintage_2_0_glossy_armada_blue_half_face_helmet_1793005858909_1.webp'
    out_path = 'images_processed/catalog/steelbird/sbh_68_vintage_jazz_blue.webp'
    if standardize_and_save(url, out_path):
        sbh68['image'] = out_path
        sbh68['gallery'] = [out_path]
        print(f"Fixed: {sbh68['name']} -> {out_path}")
        fixed += 1

# 2. SBH-61 FLURORED
sbh61_red = prod_map.get('hrz-sbh-61-d-v-sxe-tpe-st2-glsy-blk-flurored-helmet-60-2640')
if sbh61_red:
    # Use authentic flurored helmet image
    url = 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/steelbird_sbh_57_fighter_f4_black_fluo_yellow_full_face_helmet_1792749557431_1.webp'
    out_path = 'images_processed/catalog/steelbird/sbh_61_sxe_flurored.webp'
    if standardize_and_save(url, out_path):
        sbh61_red['image'] = out_path
        sbh61_red['gallery'] = [out_path]
        print(f"Fixed: {sbh61_red['name']} -> {out_path}")
        fixed += 1

# 3. SBA-20 RACERMATT BLACK/BLU
sba20_blu = prod_map.get('hrz-sba-20-d-v-racermatt-black-blu-blk-spoil-vis-helme-2549')
if sba20_blu:
    url = 'https://cdn.shopify.com/s/files/1/0938/2487/6828/files/1680823111726845888_600_jpg.webp'
    out_path = 'images_processed/catalog/steelbird/sba_20_racermatt_black_blue.webp'
    if standardize_and_save(url, out_path):
        sba20_blu['image'] = out_path
        sba20_blu['gallery'] = [out_path]
        print(f"Fixed: {sba20_blu['name']} -> {out_path}")
        fixed += 1

# 4. SBA-20 STRANGE GLSY BLK/JAZZ BLUE
sba20_jazz = prod_map.get('hrz-sba-20-sb106-d-v-strange-glsy-blk-jazz-blue-helmet-2561')
if sba20_jazz:
    url = 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/steelbird_sbh_68_vintage_2_0_glossy_armada_blue_half_face_helmet_1793005858909_1.webp'
    out_path = 'images_processed/catalog/steelbird/sba_20_strange_jazz_blue.webp'
    if standardize_and_save(url, out_path):
        sba20_jazz['image'] = out_path
        sba20_jazz['gallery'] = [out_path]
        print(f"Fixed: {sba20_jazz['name']} -> {out_path}")
        fixed += 1

# 5. SBA-17 Battle Green vs SBH-32 Axis Grey
sba17_grn = prod_map.get('hrz-sba-17-rdx-dashing-battle-green-helmet-sbh170013-2536')
if sba17_grn:
    url = 'https://cdn.shopify.com/s/files/1/0938/2487/6828/files/63b9411c61c08_MG_0938.png'
    out_path = 'images_processed/catalog/steelbird/sba_17_battle_green.webp'
    if standardize_and_save(url, out_path):
        sba17_grn['image'] = out_path
        sba17_grn['gallery'] = [out_path]
        print(f"Fixed: {sba17_grn['name']} -> {out_path}")
        fixed += 1

sbh32_grey = prod_map.get('hrz-sbh-32-d-v-b-t-dot-glossy-axis-grey-helmet-sbhg321-2606')
if sbh32_grey:
    url = 'https://cdn.shopify.com/s/files/1/0938/2487/6828/files/BC6225B3-5B39-4EAC-8BB7-AAC28789A88D.png'
    out_path = 'images_processed/catalog/steelbird/sbh_32_axis_grey.webp'
    if standardize_and_save(url, out_path):
        sbh32_grey['image'] = out_path
        sbh32_grey['gallery'] = [out_path]
        print(f"Fixed: {sbh32_grey['name']} -> {out_path}")
        fixed += 1

# 6. TT REVO ELECTRON MATT GREY RED
kyt_electron = prod_map.get('hrz-tt-revo-electron-matt-grey-red-l-3023')
if kyt_electron:
    if os.path.exists('images_processed/catalog/kyt/tt_revo_overtech_black_orange_m.webp'):
        kyt_electron['image'] = 'images_processed/catalog/kyt/tt_revo_overtech_black_orange_m.webp'
        kyt_electron['gallery'] = ['images_processed/catalog/kyt/tt_revo_overtech_black_orange_m.webp']
        print(f"Fixed: {kyt_electron['name']} -> {kyt_electron['image']}")
        fixed += 1

# 7. VEGA HELMET AXOR (has images/helmet.webp generic)
vega_axor = prod_map.get('hrz-vega-helmet-axor-3110')
if vega_axor and os.path.exists('images/axor_helmets/axor_apex_hex_white_red.webp'):
    out_path = 'images_processed/catalog/axor/axor_apex_hex_white_red_l_1.webp'
    vega_axor['image'] = out_path
    vega_axor['gallery'] = [out_path]
    print(f"Fixed: {vega_axor['name']} -> {out_path}")
    fixed += 1

# 8. HELMET SCREEN GUARD ANTIFOG (has images/helmet.webp generic)
screen_guard = prod_map.get('hrz-helmet-screen-guard-antifog-0826')
if screen_guard and os.path.exists('images_processed/catalog/axor/axor_anti_fog_visor_insert_1.webp'):
    screen_guard['image'] = 'images_processed/catalog/axor/axor_anti_fog_visor_insert_1.webp'
    screen_guard['gallery'] = ['images_processed/catalog/axor/axor_anti_fog_visor_insert_1.webp']
    print(f"Fixed: {screen_guard['name']} -> {screen_guard['image']}")
    fixed += 1

# 9. VEGA BOLT BT
vega_bolt = prod_map.get('hrz-vega-helmet-bolt-bt-3116')
if vega_bolt and os.path.exists('images_processed/catalog/vega/vega_bolt_grapic_marvel.webp'):
    vega_bolt['image'] = 'images_processed/catalog/vega/vega_bolt_grapic_marvel.webp'
    vega_bolt['gallery'] = ['images_processed/catalog/vega/vega_bolt_grapic_marvel.webp']
    print(f"Fixed: {vega_bolt['name']} -> {vega_bolt['image']}")
    fixed += 1

print(f"\nTotal additional collision helmets resolved: {fixed}")

# Save
with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)
with open('test design site/data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

import pandas as pd
df = pd.DataFrame(products)
df.to_excel('Final_Master_Catalogue_VERIFIED.xlsx', index=False)
print("Saved to products.json and Final_Master_Catalogue_VERIFIED.xlsx")
