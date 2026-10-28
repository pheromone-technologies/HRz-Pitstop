import json
import os
import io
import requests
import rembg
from PIL import Image
import numpy as np
import openpyxl

from image_standardizer import standardize_and_save

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def clean_and_standardize(src_im, dest_rel_path):
    print(f"Cleaning background & standardizing -> {dest_rel_path} ...")
    clean_rgba = rembg.remove(src_im)
    success = standardize_and_save(clean_rgba, dest_rel_path)
    return success

# STEP 1: Process Background Removal for User's Targets
print("\n=== STEP 1: Processing Clean Background Images ===")

# 1. SBH-68 Vintage Jazz Blue
if os.path.exists('scratch/sbh68_vintage_jazz_blue_rembg.png'):
    im_sbh68_blue = Image.open('scratch/sbh68_vintage_jazz_blue_rembg.png')
    standardize_and_save(im_sbh68_blue, 'images_processed/catalog/steelbird/sbh_68_vintage_jazz_blue.webp')
    print("  -> SBH-68 Vintage Jazz Blue background removed and standardized.")

# 2. SBH-68 Additional Color Variants
sbh68_colors = {
    'Cherry Red': 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/steelbird_sbh_68_vintage_2_0_glossy_cherry_red_half_face_helmet_1793006056945_1.webp?v=1793006067',
    'Battle Green': 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/steelbird_sbh_68_vintage_2_0_matt_battle_green_half_face_helmet_1793006006422_1.webp?v=1793006031',
    'White': 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/steelbird_sbh_68_vintage_2_0_white_half_face_helmet_1793005686695_1.webp?v=1793005714',
    'Silver': 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/steelbird_sbh_68_vintage_2_0_glossy_silver_half_face_helmet_1793005970683_1.webp?v=1793005992'
}
sbh68_img_map = {
    'Glossy Jazz Blue': 'images_processed/catalog/steelbird/sbh_68_vintage_jazz_blue.webp'
}

for c_name, c_url in sbh68_colors.items():
    dest_path = f"images_processed/catalog/steelbird/sbh_68_vintage_{c_name.lower().replace(' ', '_')}.webp"
    sbh68_img_map[c_name] = dest_path
    try:
        r = requests.get(c_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            im = Image.open(io.BytesIO(r.content))
            clean_and_standardize(im, dest_path)
            print(f"  -> SBH-68 {c_name} saved to {dest_path}")
    except Exception as e:
        print(f"Error fetching SBH-68 {c_name}: {e}")

# Also update existing silver file
if os.path.exists('images_processed/catalog/steelbird/sbh_68_vintage_silver.webp'):
    im_silver = Image.open('images_processed/catalog/steelbird/sbh_68_vintage_silver.webp')
    standardize_and_save(im_silver, 'images_processed/catalog/steelbird/sbh-68_d_v_vintage_dot_2_0_glsy_silver_helmet.webp')

# 3. SBH-61 Matt Black
if os.path.exists('scratch/sbh61_matt_black_rembg.png'):
    im_sbh61_matt = Image.open('scratch/sbh61_matt_black_rembg.png')
    standardize_and_save(im_sbh61_matt, 'images_processed/catalog/steelbird/sbh_61_sxe_afs_matt_black.webp')
    print("  -> SBH-61 Matt Black background removed and standardized.")

# 4. SBH-61 Cyan Green
if os.path.exists('scratch/sbh61_cyan_green_real.webp'):
    im_sbh61_cyan = Image.open('scratch/sbh61_cyan_green_real.webp')
    clean_and_standardize(im_sbh61_cyan, 'images_processed/catalog/steelbird/sbh-61_d_v_sxe_tpe_st2_matt_blk_cyangreen_helmet_580_1.webp')
    print("  -> SBH-61 Cyan Green clean studio image saved.")

# 5. SBA-20 Glossy Black
if os.path.exists('scratch/sba20_glossy_black_rembg.png'):
    im_sba20_blk = Image.open('scratch/sba20_glossy_black_rembg.png')
    standardize_and_save(im_sba20_blk, 'images_processed/catalog/steelbird/sba_20_glossy_black_racer.webp')
    standardize_and_save(im_sba20_blk, 'images_processed/catalog/unbranded/sba-20_d_v_glossy_black_blk_spoil_vis_helmet_sbh200512.webp')
    print("  -> SBA-20 Glossy Black background removed and standardized.")


# STEP 2: Construct Verified Variant Arrays for SBH-61, SBA-20, SBH-68
print("\n=== STEP 2: Assembling Color Variant Swatches ===")

# SBH-61 Variants
sbh61_variants_template = [
    {
        "id": "hrz-sbh-61-d-v-sxe-afs-edition-matt-blk-helmet-580mm-2681",
        "color": "Matt Black",
        "sku": "SBH61-MB",
        "price": 1299,
        "image": "images_processed/catalog/steelbird/sbh_61_sxe_afs_matt_black.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh_61_sxe_afs_matt_black.webp"]
    },
    {
        "id": "hrz-sbh-61-d-v-sxe-afs-edition-glsy-blk-helmet-600mm-2632",
        "color": "Glossy Black",
        "sku": "SBH61-GB",
        "price": 1299,
        "image": "images_processed/catalog/steelbird/sbh_61_sxe_afs_gloss_black.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh_61_sxe_afs_gloss_black.webp"]
    },
    {
        "id": "hrz-sbh-61-d-v-sxe-afs-sp3-glsy-blk-blue-helmet-600mm--2636",
        "color": "Black/Blue",
        "sku": "SBH611908",
        "price": 1299,
        "image": "images_processed/catalog/unbranded/sbh-61_d_v_sxe_afs_sp3_glsy_blk_blue_helmet_600mm_sbh61.webp",
        "gallery": ["images_processed/catalog/unbranded/sbh-61_d_v_sxe_afs_sp3_glsy_blk_blue_helmet_600mm_sbh61.webp"]
    },
    {
        "id": "hrz-sbh-61-d-v-sxe-tpe-st2-glsy-blk-flurored-helmet-60-2640",
        "color": "Fluro-Red",
        "sku": "SBH61-FR",
        "price": 3599,
        "image": "images_processed/catalog/steelbird/sbh-61_d_v_sxe_tpe_st2_glsy_blk_flurored_helmet_600mm.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh-61_d_v_sxe_tpe_st2_glsy_blk_flurored_helmet_600mm.webp"]
    },
    {
        "id": "hrz-sbh-61-d-v-sxe-tpe-st2-matt-blk-cyangreen-helmet-5-2675",
        "color": "Black/Cyan Green",
        "sku": "SBH61-CG",
        "price": 3599,
        "image": "images_processed/catalog/steelbird/sbh-61_d_v_sxe_tpe_st2_matt_blk_cyangreen_helmet_580_1.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh-61_d_v_sxe_tpe_st2_matt_blk_cyangreen_helmet_580_1.webp"]
    }
]

# SBA-20 Variants
sba20_variants_template = [
    {
        "id": "hrz-sba-20-d-v-glossy-black-blk-spoil-vis-helmet-sbh20-2544",
        "color": "Glossy Black",
        "sku": "SBH200512",
        "price": 2499,
        "image": "images_processed/catalog/steelbird/sba_20_glossy_black_racer.webp",
        "gallery": ["images_processed/catalog/steelbird/sba_20_glossy_black_racer.webp"]
    },
    {
        "id": "hrz-sba-20-d-v-09-b-t-glossy-black-blue-helmet-sbh2016-2540",
        "color": "Black/Blue",
        "sku": "SBH201681",
        "price": 2799,
        "image": "images_processed/catalog/unbranded/sba-20_d_v_09_b_t_glossy_black_blue_helmet_sbh201681.webp",
        "gallery": ["images_processed/catalog/unbranded/sba-20_d_v_09_b_t_glossy_black_blue_helmet_sbh201681.webp"]
    },
    {
        "id": "hrz-sba-20-d-v-shield-x-b-t-glossy-black-red-helmet-sb-2551",
        "color": "Black/Red",
        "sku": "SBH201714",
        "price": 2799,
        "image": "images_processed/catalog/steelbird/sba-20_d_v_shield_x_b_t_glossy_black_red_helmet_sbh201714.webp",
        "gallery": ["images_processed/catalog/steelbird/sba-20_d_v_shield_x_b_t_glossy_black_red_helmet_sbh201714.webp"]
    },
    {
        "id": "hrz-sba-20-d-v-09-b-t-glossy-black-neon-helmet-sbh2016-2559",
        "color": "Black/Neon",
        "sku": "SBH201684",
        "price": 2799,
        "image": "images_processed/catalog/unbranded/sba-20_d_v_09_b_t_glossy_black_neon_helmet_sbh201684.webp",
        "gallery": ["images_processed/catalog/unbranded/sba-20_d_v_09_b_t_glossy_black_neon_helmet_sbh201684.webp"]
    },
    {
        "id": "hrz-sba-20-sb106-d-v-strange-glsy-blk-jazz-blue-helmet-2561",
        "color": "Jazz Blue",
        "sku": "SBH106066",
        "price": 2799,
        "image": "images_processed/catalog/steelbird/sba_20_strange_jazz_blue.webp",
        "gallery": ["images_processed/catalog/steelbird/sba_20_strange_jazz_blue.webp"]
    },
    {
        "id": "hrz-sba-20-d-v-silver-born-to-ride-glsy-blk-grey-helme-2555",
        "color": "Black/Grey",
        "sku": "SBH20-GR",
        "price": 2799,
        "image": "images_processed/catalog/steelbird/sbh-20_sb_106_d_v_strange_glsy_blk_grey_helmet.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh-20_sb_106_d_v_strange_glsy_blk_grey_helmet.webp"]
    }
]

# SBH-68 Variants
sbh68_variants_template = [
    {
        "id": "hrz-sbh-68-d-v-vintage-dot-2-0-glsy-jazz-blue-helmet-2642",
        "color": "Glossy Jazz Blue",
        "sku": "SBH68-JB",
        "price": 1499,
        "image": "images_processed/catalog/steelbird/sbh_68_vintage_jazz_blue.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh_68_vintage_jazz_blue.webp"]
    },
    {
        "id": "hrz-sbh-68-d-v-vintage-dot-2-0-glsy-silver-helmet-2644",
        "color": "Glossy Silver",
        "sku": "SBH68-SL",
        "price": 1499,
        "image": "images_processed/catalog/steelbird/sbh-68_d_v_vintage_dot_2_0_glsy_silver_helmet.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh-68_d_v_vintage_dot_2_0_glsy_silver_helmet.webp"]
    },
    {
        "id": "hrz-sbh-68-cherry-red",
        "color": "Cherry Red",
        "sku": "SBH68-CR",
        "price": 1499,
        "image": "images_processed/catalog/steelbird/sbh_68_vintage_cherry_red.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh_68_vintage_cherry_red.webp"]
    },
    {
        "id": "hrz-sbh-68-battle-green",
        "color": "Battle Green",
        "sku": "SBH68-BG",
        "price": 1499,
        "image": "images_processed/catalog/steelbird/sbh_68_vintage_battle_green.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh_68_vintage_battle_green.webp"]
    },
    {
        "id": "hrz-sbh-68-white",
        "color": "Glossy White",
        "sku": "SBH68-WH",
        "price": 1499,
        "image": "images_processed/catalog/steelbird/sbh_68_vintage_white.webp",
        "gallery": ["images_processed/catalog/steelbird/sbh_68_vintage_white.webp"]
    }
]

# STEP 3: Update products.json and test design site
print("\n=== STEP 3: Applying to Catalog JSONs ===")
catalog_files = ['data/products.json', 'test design site/data/products.json']

for cat_file in catalog_files:
    with open(cat_file, 'r', encoding='utf-8') as f:
        prods = json.load(f)

    for p in prods:
        pid = p['id']
        name_up = p['name'].upper()

        # Update SBH-61 products
        if 'SBH-61' in name_up or 'SBH 61' in name_up:
            p['variants'] = [dict(v) for v in sbh61_variants_template]
            if 'MATT BLK' in name_up and 'BLUE' not in name_up:
                p['image'] = "images_processed/catalog/steelbird/sbh_61_sxe_afs_matt_black.webp"
                p['gallery'] = ["images_processed/catalog/steelbird/sbh_61_sxe_afs_matt_black.webp"]
            elif 'CYANGREEN' in name_up or 'CYAN' in name_up:
                p['image'] = "images_processed/catalog/steelbird/sbh-61_d_v_sxe_tpe_st2_matt_blk_cyangreen_helmet_580_1.webp"
                p['gallery'] = ["images_processed/catalog/steelbird/sbh-61_d_v_sxe_tpe_st2_matt_blk_cyangreen_helmet_580_1.webp"]
            elif 'FLURORED' in name_up:
                p['image'] = "images_processed/catalog/steelbird/sbh-61_d_v_sxe_tpe_st2_glsy_blk_flurored_helmet_600mm.webp"
                p['gallery'] = ["images_processed/catalog/steelbird/sbh-61_d_v_sxe_tpe_st2_glsy_blk_flurored_helmet_600mm.webp"]
            elif 'GLSY BLK' in name_up and 'BLUE' not in name_up:
                p['image'] = "images_processed/catalog/steelbird/sbh_61_sxe_afs_gloss_black.webp"
                p['gallery'] = ["images_processed/catalog/steelbird/sbh_61_sxe_afs_gloss_black.webp"]

        # Update SBA-20 products
        elif 'SBA-20' in name_up or 'SBA 20' in name_up:
            p['variants'] = [dict(v) for v in sba20_variants_template]
            if 'GLOSSY BLACK + BLK SPOIL' in name_up or 'GLOSSY BLACK +BLK SPOIL' in name_up:
                p['image'] = "images_processed/catalog/steelbird/sba_20_glossy_black_racer.webp"
                p['gallery'] = ["images_processed/catalog/steelbird/sba_20_glossy_black_racer.webp"]
            elif 'JAZZ BLUE' in name_up:
                p['image'] = "images_processed/catalog/steelbird/sba_20_strange_jazz_blue.webp"
                p['gallery'] = ["images_processed/catalog/steelbird/sba_20_strange_jazz_blue.webp"]

        # Update SBH-68 products
        elif 'SBH-68' in name_up or 'SBH 68' in name_up:
            p['variants'] = [dict(v) for v in sbh68_variants_template]
            if 'JAZZ BLUE' in name_up:
                p['image'] = "images_processed/catalog/steelbird/sbh_68_vintage_jazz_blue.webp"
                p['gallery'] = ["images_processed/catalog/steelbird/sbh_68_vintage_jazz_blue.webp"]
            elif 'SILVER' in name_up:
                p['image'] = "images_processed/catalog/steelbird/sbh-68_d_v_vintage_dot_2_0_glsy_silver_helmet.webp"
                p['gallery'] = ["images_processed/catalog/steelbird/sbh-68_d_v_vintage_dot_2_0_glsy_silver_helmet.webp"]

    with open(cat_file, 'w', encoding='utf-8') as f:
        json.dump(prods, f, indent=2, ensure_ascii=False)
    print(f"Saved updated catalog to {cat_file}")

# STEP 4: Update Master Excel Sheet
wb_path = 'Final_Master_Catalogue_VERIFIED.xlsx'
if os.path.exists(wb_path):
    wb = openpyxl.load_workbook(wb_path)
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    id_col = headers.index('ID') + 1 if 'ID' in headers else 1
    img_col = headers.index('Image URL') + 1 if 'Image URL' in headers else (headers.index('IMAGE') + 1 if 'IMAGE' in headers else None)
    
    with open('data/products.json', 'r', encoding='utf-8') as f:
        prods = json.load(f)
    id_map = {p['id']: p['image'] for p in prods}

    if img_col:
        for row in range(2, ws.max_row + 1):
            pid = ws.cell(row=row, column=id_col).value
            if pid in id_map:
                ws.cell(row=row, column=img_col).value = id_map[pid]
        wb.save(wb_path)
        print("Updated Final_Master_Catalogue_VERIFIED.xlsx")

print("\n=== ALL TARGET ASSETS AND VARIANTS SUCCESSFULLY BUILT AND LINKED ===")
