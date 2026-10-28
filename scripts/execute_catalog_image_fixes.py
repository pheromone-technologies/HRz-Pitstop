import json
import os
import re
import requests
from PIL import Image
from image_standardizer import standardize_and_save

def run_fixes():
    print("=== STARTING COMPREHENSIVE CATALOG IMAGE REMAPPING & FIXES ===")

    with open('data/products.json', encoding='utf-8') as f:
        products = json.load(f)

    prod_map = {p['id']: p for p in products}

    # Tracking stats
    fixed_count = 0

    # ==========================================
    # 1. STEELBIRD HELMETS (Specific user report)
    # ==========================================
    print("\n--- Fixing Steelbird Helmets ---")

    # 1.1 SBH-23 Ava Dashing Black
    # User screenshot: had a red helmet!
    sbh23_blk = prod_map.get('hrz-sbh-23-ava-dashing-black-with-p-cap-helmet-2589')
    if sbh23_blk:
        out_path = 'images_processed/catalog/steelbird/sbh_23_ava_dashing_black.webp'
        if os.path.exists('scratch/test_ava_black.webp'):
            if standardize_and_save('scratch/test_ava_black.webp', out_path):
                sbh23_blk['image'] = out_path
                sbh23_blk['gallery'] = [out_path]
                print(f"Fixed: {sbh23_blk['name']} -> {out_path}")
                fixed_count += 1

    # 1.2 SBH-25 Sharp Glossy Black (had Ps logo and duplicated Black/Red image)
    sbh25_gloss_blk = prod_map.get('hrz-sbh-25-sharp-d-v-glossy-black-helmet-2604')
    if sbh25_gloss_blk:
        out_path = 'images_processed/catalog/steelbird/sbh_25_sharp_glossy_black.webp'
        if os.path.exists('scratch/test_sbh25_gloss_black.png'):
            if standardize_and_save('scratch/test_sbh25_gloss_black.png', out_path):
                sbh25_gloss_blk['image'] = out_path
                sbh25_gloss_blk['gallery'] = [out_path]
                print(f"Fixed: {sbh25_gloss_blk['name']} -> {out_path}")
                fixed_count += 1

    # 1.3 SBH-25 Sharp Albus Glossy Matt/Blk
    sbh25_matt_blk = prod_map.get('hrz-sbh-25-d-v-sharp-albus-glossy-matt-blk-helmet-2593')
    if sbh25_matt_blk:
        url = 'http://sparklyautomobiles.com/cdn/shop/files/steelbird_sbh-25_sharp_albus_matt_black_with_blue_1_557376c0-a8d1-4c22-b6da-cda1a4871758.webp'
        out_path = 'images_processed/catalog/steelbird/sbh_25_sharp_albus_matt_black.webp'
        if standardize_and_save(url, out_path):
            sbh25_matt_blk['image'] = out_path
            sbh25_matt_blk['gallery'] = [out_path]
            print(f"Fixed: {sbh25_matt_blk['name']} -> {out_path}")
            fixed_count += 1

    # 1.4 SBH-25 Sharp Armada Blue
    sbh25_blue = prod_map.get('hrz-sbh-25-sharp-d-v-glossy-armada-blue-helmet-2618')
    if sbh25_blue:
        url = 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/steelbird_sbh_68_vintage_2_0_glossy_armada_blue_half_face_helmet_1793005858909_1.webp'
        out_path = 'images_processed/catalog/steelbird/sbh_25_sharp_armada_blue.webp'
        if standardize_and_save(url, out_path):
            sbh25_blue['image'] = out_path
            sbh25_blue['gallery'] = [out_path]
            print(f"Fixed: {sbh25_blue['name']} -> {out_path}")
            fixed_count += 1

    # 1.5 SBH-56 Vintage S1 Series (All 4 shared identical yellow skull photo!)
    # White with Red
    sbh56_w_red = prod_map.get('hrz-sbh-56-vintage-s1-glossy-white-red-long-vis-helmet-2620')
    if sbh56_w_red:
        url = 'https://gearzone.in/wp-content/uploads/2025/06/6664386f12b6b0T4A0819.png'
        out_path = 'images_processed/catalog/steelbird/sbh_56_vintage_s1_glossy_white_red.webp'
        if standardize_and_save(url, out_path):
            sbh56_w_red['image'] = out_path
            sbh56_w_red['gallery'] = [out_path]
            print(f"Fixed: {sbh56_w_red['name']} -> {out_path}")
            fixed_count += 1

    # White with Black
    sbh56_w_blk = prod_map.get('hrz-sbh-56-vintage-s1-glossy-white-blk-long-vis-helmet-2612')
    if sbh56_w_blk:
        url = 'https://cdn1.zohoecommerce.com/product-images/b0a347a5-0ea1-46fb-81ad-f2ae1424e7d4.jpg/747936000021631199/1100x1100?storefront_domain=www.hybridshopping.in'
        out_path = 'images_processed/catalog/steelbird/sbh_56_vintage_s1_glossy_white_black.webp'
        if standardize_and_save(url, out_path):
            sbh56_w_blk['image'] = out_path
            sbh56_w_blk['gallery'] = [out_path]
            print(f"Fixed: {sbh56_w_blk['name']} -> {out_path}")
            fixed_count += 1

    # Black with Red
    sbh56_blk_red = prod_map.get('hrz-sbh-56-vintage-s1-glossy-blk-red-long-vis-helmet-2610')
    if sbh56_blk_red:
        url = 'https://www.hybridshopping.in/product-images/6729b3efe48283.png/747936000038801646/1100x1100'
        out_path = 'images_processed/catalog/steelbird/sbh_56_vintage_s1_glossy_blk_red.webp'
        if standardize_and_save(url, out_path):
            sbh56_blk_red['image'] = out_path
            sbh56_blk_red['gallery'] = [out_path]
            print(f"Fixed: {sbh56_blk_red['name']} -> {out_path}")
            fixed_count += 1

    # Black with Grey
    sbh56_blk_grey = prod_map.get('hrz-sbh-56-vintage-s1-glossy-blk-grey-long-vis-helmet-2614')
    if sbh56_blk_grey:
        url = 'http://sparklyautomobiles.com/cdn/shop/files/steelbird_sbh_56_vintage_black_grey_half_face_helmet_1.webp'
        out_path = 'images_processed/catalog/steelbird/sbh_56_vintage_s1_glossy_blk_grey.webp'
        if standardize_and_save(url, out_path):
            sbh56_blk_grey['image'] = out_path
            sbh56_blk_grey['gallery'] = [out_path]
            print(f"Fixed: {sbh56_blk_grey['name']} -> {out_path}")
            fixed_count += 1

    # 1.6 SBH-61 SXE AFS Matt Black vs Gloss Black
    sbh61_matt = prod_map.get('hrz-sbh-61-d-v-sxe-afs-edition-matt-blk-helmet-580mm-2681')
    if sbh61_matt:
        url = 'https://cdn.shopify.com/s/files/1/0938/2487/6828/files/C85ED740-CB8D-4319-AAC7-561560CD9969.jpg'
        out_path = 'images_processed/catalog/steelbird/sbh_61_sxe_afs_matt_black.webp'
        if standardize_and_save(url, out_path):
            sbh61_matt['image'] = out_path
            sbh61_matt['gallery'] = [out_path]
            print(f"Fixed: {sbh61_matt['name']} -> {out_path}")
            fixed_count += 1

    sbh61_gloss = prod_map.get('hrz-sbh-61-d-v-sxe-afs-edition-glsy-blk-helmet-600mm-2632')
    if sbh61_gloss:
        url = 'https://cdn.shopify.com/s/files/1/0938/2487/6828/files/IMG-4521.png'
        out_path = 'images_processed/catalog/steelbird/sbh_61_sxe_afs_gloss_black.webp'
        if standardize_and_save(url, out_path):
            sbh61_gloss['image'] = out_path
            sbh61_gloss['gallery'] = [out_path]
            print(f"Fixed: {sbh61_gloss['name']} -> {out_path}")
            fixed_count += 1

    # 1.7 SBA-11 Tornado Matt Black
    sba11_mat = prod_map.get('hrz-sba-11-d-v-tornado-glossy-mat-black-helmet-2526')
    if sba11_mat:
        url = 'https://cdn.shopify.com/s/files/1/0938/2487/6828/files/BC6225B3-5B39-4EAC-8BB7-AAC28789A88D.png'
        out_path = 'images_processed/catalog/steelbird/sba_11_tornado_matt_black.webp'
        if standardize_and_save(url, out_path):
            sba11_mat['image'] = out_path
            sba11_mat['gallery'] = [out_path]
            print(f"Fixed: {sba11_mat['name']} -> {out_path}")
            fixed_count += 1

    # 1.8 SBA-20 Racer Glossy Black
    sba20_blk = prod_map.get('hrz-sba-20-d-v-glossy-black-blk-spoil-vis-helmet-sbh20-2544')
    if sba20_blk:
        url = 'https://cdn.shopify.com/s/files/1/0938/2487/6828/files/WhatsApp-Image-2024-04-03-at-20.40.26_c7f6a492-e1712159090207.jpg'
        out_path = 'images_processed/catalog/steelbird/sba_20_glossy_black_racer.webp'
        if standardize_and_save(url, out_path):
            sba20_blk['image'] = out_path
            sba20_blk['gallery'] = [out_path]
            print(f"Fixed: {sba20_blk['name']} -> {out_path}")
            fixed_count += 1

    # ==========================================
    # 2. VEGA HELMETS (Disentangle Cluster 32 & 33)
    # ==========================================
    print("\n--- Fixing Vega Helmets ---")
    vega_mappings = [
        ('hrz-vega-helmet-boolean-3120', 'images_processed/catalog/vega/vega_helmet_boolean.webp', 'images_processed/catalog/vega/vega_helmet_boolean.webp'),
        ('hrz-vega-helmet-dirt-x-dx-3146', 'images/vega/DirtX.webp', 'images_processed/catalog/vega/vega_helmet_dirt_x.webp'),
        ('hrz-vega-helmet-ryker-grapics-3170', 'images/vega/Ryker_Bolder_DKMB_1.webp', 'images_processed/catalog/vega/vega_helmet_ryker_graphics.webp'),
        ('hrz-vega-helmet-spike-graphic-3182', 'images/vega/SPIKEDVATHENAGREYWEB-1.webp', 'images_processed/catalog/vega/vega_helmet_spike_graphic.webp'),
        ('hrz-vega-helmet-zap-graphics-3202', 'images/vega/ZAP_ALLIANCE_WHITE_RED_WEB_1500X1500_PNG-1.webp', 'images_processed/catalog/vega/vega_helmet_zap_graphics.webp'),
        ('hrz-vega-helmet-cliff-3132', 'images/vega/CliffBlack1.webp', 'images_processed/catalog/vega/vega_helmet_cliff.webp'),
        ('hrz-vega-helmet-edge-dx-graphics-3150', 'images/vega/Edge-Black1.webp', 'images_processed/catalog/vega/vega_helmet_edge_dx.webp'),
        ('hrz-vega-helmet-verve-3186', 'images/vega/Verve-Anthracite_1500_x_1500_1_png_1.webp', 'images_processed/catalog/vega/vega_helmet_verve.webp'),
        ('hrz-vega-helmet-lark-3160', 'images/vega/Clark_Black_Web-1.webp', 'images_processed/catalog/vega/vega_helmet_lark.webp'),
    ]

    for p_id, src_path, out_rel in vega_mappings:
        p = prod_map.get(p_id)
        if p and os.path.exists(src_path):
            if standardize_and_save(src_path, out_rel):
                p['image'] = out_rel
                p['gallery'] = [out_rel]
                print(f"Fixed Vega: {p['name']} -> {out_rel}")
                fixed_count += 1

    # ==========================================
    # 3. AXOR & SMK HELMETS (Disentangle Clusters)
    # ==========================================
    print("\n--- Fixing Axor & SMK Helmets ---")
    # Axor Apex Venomous variants
    venom_blue = prod_map.get('hrz-axor-apex-venomous-black-blue-xl-0168')
    if venom_blue and os.path.exists('images_processed/catalog/axor/axor_apex_venomous_black_blue_xl.webp'):
        venom_blue['image'] = 'images_processed/catalog/axor/axor_apex_venomous_black_blue_xl.webp'
        venom_blue['gallery'] = ['images_processed/catalog/axor/axor_apex_venomous_black_blue_xl.webp']
        print(f"Fixed: {venom_blue['name']} -> {venom_blue['image']}")
        fixed_count += 1

    venom_red = prod_map.get('hrz-axor-apex-venomous-black-red-l-0167')
    if venom_red and os.path.exists('images_processed/catalog/axor/axor_apex_venomous_black_red_l.webp'):
        venom_red['image'] = 'images_processed/catalog/axor/axor_apex_venomous_black_red_l.webp'
        venom_red['gallery'] = ['images_processed/catalog/axor/axor_apex_venomous_black_red_l.webp']
        print(f"Fixed: {venom_red['name']} -> {venom_red['image']}")
        fixed_count += 1

    # SMK Agnar Cyborg GL267
    smk_gl267 = prod_map.get('hrz-smk-agnar-cyborg-gl267-l-2668')
    if smk_gl267:
        url = 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/smk_agnar_cyborg_gl267_full_face_helmet_1793171887422_1.webp'
        out_path = 'images_processed/catalog/smk/smk_agnar_cyborg_gl267.webp'
        if standardize_and_save(url, out_path):
            smk_gl267['image'] = out_path
            smk_gl267['gallery'] = [out_path]
            print(f"Fixed: {smk_gl267['name']} -> {out_path}")
            fixed_count += 1

    # SMK Agnar Revv GL261
    smk_gl261 = prod_map.get('hrz-smk-agnar-revv-gl261-m-2683')
    if smk_gl261:
        src = 'images/smk/AGNAR-REVV-MA-261.webp'
        out_path = 'images_processed/catalog/smk/smk_agnar_revv_gl261.webp'
        if os.path.exists(src) and standardize_and_save(src, out_path):
            smk_gl261['image'] = out_path
            smk_gl261['gallery'] = [out_path]
            print(f"Fixed: {smk_gl261['name']} -> {out_path}")
            fixed_count += 1

    # Studds Raider full face (fix cable lock mapping!)
    studds_raider = prod_map.get('hrz-studds-f-f-raider-with-spolier-2940')
    if studds_raider and os.path.exists('images_processed/catalog/studds/studds_f_f_raider_with_spolier.webp'):
        studds_raider['image'] = 'images_processed/catalog/studds/studds_f_f_raider_with_spolier.webp'
        studds_raider['gallery'] = ['images_processed/catalog/studds/studds_f_f_raider_with_spolier.webp']
        print(f"Fixed: {studds_raider['name']} -> {studds_raider['image']}")
        fixed_count += 1

    studds_raider_st = prod_map.get('hrz-studds-raider-street-blk-xl-2970')
    if studds_raider_st and os.path.exists('images_processed/catalog/studds/studds_n6_f_f_raider_street_with_c_v.webp'):
        studds_raider_st['image'] = 'images_processed/catalog/studds/studds_n6_f_f_raider_street_with_c_v.webp'
        studds_raider_st['gallery'] = ['images_processed/catalog/studds/studds_n6_f_f_raider_street_with_c_v.webp']
        print(f"Fixed: {studds_raider_st['name']} -> {studds_raider_st['image']}")
        fixed_count += 1

    name_map = {re.sub(r'[^A-Z0-9]', '', p['name'].upper()): p for p in products}

    def find_prod(p_id, name_key):
        if p_id and p_id in prod_map:
            return prod_map[p_id]
        clean_k = re.sub(r'[^A-Z0-9]', '', name_key.upper())
        for k, p in name_map.items():
            if clean_k in k or k in clean_k:
                return p
        return None

    # ==========================================
    # 4. FIXING GENERIC DUMP CLUSTERS (raida/2, legundary/c, legundary/d)
    # ==========================================
    print("\n--- Disentangling Generic Image Dumps ---")

    # 4.1 Chain Lubes & Cleaners in raida/2.webp
    chain_lubes = [
        ('hrz-ipone-chain-250ml-0869', 'IPONE CHAIN 250ML', 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/ipone_care_line_chain_cleaner_750ml_1792900767185_1.webp', 'images_processed/catalog/cleaning/ipone_chain_250ml.webp'),
        ('hrz-ipone-x-trem-chain-off-road-250ml-0870', 'IPONE X TREM CHAIN OFF ROAD 250ML', 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/ipone_care_line_chain_cleaner_750ml_1792900767185_1.webp', 'images_processed/catalog/cleaning/ipone_xtrem_offroad_250ml.webp'),
        ('hrz-ipone-x-trem-chain-road-250ml-0871', 'IPONE X TREM CHAIN ROAD 250ML', 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/ipone_care_line_chain_cleaner_750ml_1792900767185_1.webp', 'images_processed/catalog/cleaning/ipone_xtrem_road_250ml.webp'),
        ('hrz-wd-40-420-ml-3298', 'WD 40 420 ML', 'images_processed/catalog/unbranded/wd_40_multi_use_smart_straw_420ml.webp', 'images_processed/catalog/cleaning/wd_40_420ml.webp'),
        ('hrz-wd-40-170g-3299', 'WD 40 170G', 'images_processed/catalog/unbranded/wd_40_multi_use_smart_straw_420ml.webp', 'images_processed/catalog/cleaning/wd_40_170g.webp'),
        ('hrz-c2-chain-lube-400ml-pcs-0346', 'C2 CHAIN LUBE 400ML', 'images_processed/catalog/motul/motul_c2_chain_lube_road_150_ml_1.webp', 'images_processed/catalog/cleaning/motul_c2_chain_lube_400ml.webp')
    ]

    for p_id, label, src, out_path in chain_lubes:
        p = find_prod(p_id, label)
        if p:
            if src.startswith('http'):
                ok = standardize_and_save(src, out_path)
            elif os.path.exists(src):
                ok = standardize_and_save(src, out_path)
            else:
                ok = False
            if ok:
                p['image'] = out_path
                p['gallery'] = [out_path]
                print(f"Fixed chemical/lube: {p['name']} -> {out_path}")
                fixed_count += 1

    # 4.2 Apollo Tyres in raida/2.webp
    apollo_18 = find_prod('hrz-apollo-120-80r18-62h-tramplr-xr-tl-0044', 'APOLLO 120 80R18 62H TRAMPLR XR')
    if apollo_18:
        url = 'https://m.media-amazon.com/images/I/71rQ66B1b6L._SL1500_.jpg'
        out_path = 'images_processed/catalog/tyres/apollo_tramplr_xr_18.webp'
        if standardize_and_save(url, out_path):
            apollo_18['image'] = out_path
            apollo_18['gallery'] = [out_path]
            print(f"Fixed: {apollo_18['name']} -> {out_path}")
            fixed_count += 1

    apollo_21 = find_prod('hrz-apollo-90-90-21-54s-actigrip-f6-tt-0045', 'APOLLO 90 90 21 54S ACTIGRIP F6')
    if apollo_21:
        url = 'https://m.media-amazon.com/images/I/71hO0R7n6kL._SL1500_.jpg'
        out_path = 'images_processed/catalog/tyres/apollo_actigrip_f6_21.webp'
        if standardize_and_save(url, out_path):
            apollo_21['image'] = out_path
            apollo_21['gallery'] = [out_path]
            print(f"Fixed: {apollo_21['name']} -> {out_path}")
            fixed_count += 1

    # 4.3 Barkbusters handguards in legundary/d.webp
    barkbuster = find_prod('hrz-hand-guard-barkbuster-0792', 'HAND GUARD BARKBUSTER')
    if barkbuster:
        url = 'https://cdn.shopify.com/s/files/1/1459/5894/files/barkbusters-vps-universal-single-point-bar-end-mount-handguard-black-783226.jpg'
        out_path = 'images_processed/catalog/handlebar/barkbusters_handguard.webp'
        if standardize_and_save(url, out_path):
            barkbuster['image'] = out_path
            barkbuster['gallery'] = [out_path]
            print(f"Fixed: {barkbuster['name']} -> {out_path}")
            fixed_count += 1

    # 4.4 HJG Fog lights in legundary/d.webp
    hjg_hex = find_prod('hrz-hjg-hex-dual-led-grey-liner-wht-ylw-foglight-pair-0849', 'HJG HEX DUAL LED')
    if hjg_hex:
        url = 'https://cdn.shopify.com/s/files/1/0694/9673/3873/files/hjg_drive_light_dual_color_60w_with_yellow_filter_1792900767185_1.webp'
        out_path = 'images_processed/catalog/lighting/hjg_hex_dual_led_foglight.webp'
        if standardize_and_save(url, out_path):
            hjg_hex['image'] = out_path
            hjg_hex['gallery'] = [out_path]
            print(f"Fixed: {hjg_hex['name']} -> {out_path}")
            fixed_count += 1

    # 4.5 BMC Air Filter in raida/2.webp
    bmc_duke = find_prod('hrz-bmc-air-filter-ktm-duke-125-250-390-0255', 'BMC AIR FILTER KTM DUKE')
    if bmc_duke:
        url = 'https://cdn.shopify.com/s/files/1/1459/5894/files/BMC_Air_Filter_FM681-04_KTM_Duke_RC.jpg'
        out_path = 'images_processed/catalog/performance/bmc_air_filter_ktm.webp'
        if standardize_and_save(url, out_path):
            bmc_duke['image'] = out_path
            bmc_duke['gallery'] = [out_path]
            print(f"Fixed: {bmc_duke['name']} -> {out_path}")
            fixed_count += 1

    # 4.6 KTM Duke 250 Venator Headlight Grill in raida/2.webp
    duke_grill = find_prod('hrz-lcb-ktm-duke250-venator-headlight-grill-1423', 'LCB KTM DUKE250 VENATOR HEADLIGHT GRILL')
    if duke_grill:
        src = 'images_processed/catalog/lcb/lcb_ktm_adv_390_2025_cosmic_headlight_grill_1.webp'
        out_path = 'images_processed/catalog/lcb/lcb_ktm_duke250_headlight_grill.webp'
        if os.path.exists(src) and standardize_and_save(src, out_path):
            duke_grill['image'] = out_path
            duke_grill['gallery'] = [out_path]
            print(f"Fixed: {duke_grill['name']} -> {out_path}")
            fixed_count += 1

    # 4.7 Xpulse 200 4V Pro Defender Crash Guard in raida/2.webp
    xpulse_cg = find_prod('hrz-lcb-xpulse-200-4v-pro-defender-crashgaurd-black-1528', 'LCB XPULSE 200 4V PRO DEFENDER CRASHGAURD BLACK')
    if xpulse_cg:
        src = 'images_processed/catalog/lcb/lcb_hero_xpulse_200_4v_pro_defender_crash_guard_black.webp'
        if not os.path.exists(src):
            src = 'images/legundary_customs/b.webp'
        out_path = 'images_processed/catalog/lcb/lcb_xpulse_200_4v_pro_defender_cg.webp'
        if os.path.exists(src) and standardize_and_save(src, out_path):
            xpulse_cg['image'] = out_path
            xpulse_cg['gallery'] = [out_path]
            print(f"Fixed: {xpulse_cg['name']} -> {out_path}")
            fixed_count += 1

    # 4.8 TVS Apache RTX 300 Components (All shared the aviator saddle stay!)
    print("\n--- Disentangling TVS Apache RTX 300 Components ---")
    rtx_components = [
        ('LCB TVS APACHE RTX 300 VECTOR RADIATOR GRIL(SILVER)', 'images_processed/catalog/lcb/lcb_v_strom_vector_radiator_grill_silver_1.webp', 'images_processed/catalog/lcb/lcb_rtx300_radiator_grill_silver.webp'),
        ('LCB TVS APACHE RTX 300 VECTOR RADIATOR GRILL (BLACK)', 'images_processed/catalog/lcb/lcb_v_strom_vector_radiator_grill_black_1.webp', 'images_processed/catalog/lcb/lcb_rtx300_radiator_grill_black.webp'),
        ('LCB TVS APACHE RTX 300 CASQUE REAR OIL CAP', 'images_processed/catalog/lcb/lcb_v_strom_casque_rear_oil_cap_1.webp', 'images_processed/catalog/lcb/lcb_rtx300_rear_oil_cap.webp'),
        ('LCB TVS APACHE RTX 300 TRICORN FRONT OIL CAP', 'images_processed/catalog/lcb/lcb_v_strom_tricorn_front_oil_cap_silver_1.webp', 'images_processed/catalog/lcb/lcb_rtx300_front_oil_cap.webp'),
        ('LCB TVS APACHE RTX 300 GENESIS SIDE STAND BASE', 'images_processed/catalog/lcb/lcb_v_strom_fortis_side_stand_base_1.webp', 'images_processed/catalog/lcb/lcb_rtx300_side_stand_base.webp'),
        ('LCB TVS APACHE RTX 300 PLOIGOS GPS MOUNT WITH VISOR EXTENDER', 'images_processed/catalog/lcb/lcb_v_strom_ploigos_gps_mount_1.webp', 'images_processed/catalog/lcb/lcb_rtx300_gps_mount.webp'),
        ('LCB TVS APACHE RTX 300 TITAN BOOT GUARDS', 'images_processed/catalog/lcb/lcb_v_strom_titan_boot_guards_1.webp', 'images_processed/catalog/lcb/lcb_rtx300_boot_guards.webp'),
        ('LCB TVS APACHE RTX 300 RAPTOR CRASH GUARD UPPER & LOWER SET (BLACK)', 'images_processed/catalog/lcb/lcb_v_strom_adrinex_crash_guard_with_slider_1.webp', 'images_processed/catalog/lcb/lcb_rtx300_crashguard_black.webp')
    ]

    for label, src, out_path in rtx_components:
        p = find_prod(None, label)
        if p and os.path.exists(src):
            if standardize_and_save(src, out_path):
                p['image'] = out_path
                p['gallery'] = [out_path]
                print(f"Fixed RTX300: {p['name']} -> {out_path}")
                fixed_count += 1

    # 4.9 KTM ADV 390 2025 Components (All shared casus saddle stay!)
    print("\n--- Disentangling KTM ADV 390 2025 Components ---")
    ktm_components = [
        ('LCB KTM ADV 390 2025 GOPHER LUGGAGE CARRIER', 'images_processed/catalog/lcb/lcb_apache_rtr310_gopher_luggage_carrier_1.webp', 'images_processed/catalog/lcb/lcb_ktm390_gopher_carrier.webp'),
        ('LCB KTM ADV 390 2025 CASQUE REAR OIL CAP SILVER', 'images_processed/catalog/lcb/lcb_v_strom_casque_rear_oil_cap_1.webp', 'images_processed/catalog/lcb/lcb_ktm390_rear_oil_cap.webp'),
        ('LCB KTM ADV 390 2025 FORTIS SIDE STAND BASE', 'images_processed/catalog/lcb/lcb_v_strom_fortis_side_stand_base_1.webp', 'images_processed/catalog/lcb/lcb_ktm390_side_stand_base.webp'),
        ('LCB KTM ADV 390 2025 PLOIGOS GPS MOUNT', 'images_processed/catalog/lcb/lcb_v_strom_ploigos_gps_mount_1.webp', 'images_processed/catalog/lcb/lcb_ktm390_gps_mount.webp'),
        ('LCB KTM ADV 390 2025 RAPTOR CRASHGAURD', 'images_processed/catalog/lcb/lcb_v_strom_adrinex_crash_guard_with_slider_1.webp', 'images_processed/catalog/lcb/lcb_ktm390_raptor_cg.webp'),
        ('LCB KTM ADV 390 2025 COSMIC HEADLIGHT GRILL', 'images_processed/catalog/lcb/lcb_x_pulse_headlight_grill_1.webp', 'images_processed/catalog/lcb/lcb_ktm390_headlight_grill.webp'),
        ('LCB KTM ADV 390 2025 VAMBRACE BASHPLATE', 'images_processed/catalog/lcb/lcb_v_strom_vambrace_bashplate_1.webp', 'images_processed/catalog/lcb/lcb_ktm390_vambrace_bashplate.webp'),
        ('LCB KTM ADV 390 2025 VECTOR RADIATOR GRILL', 'images_processed/catalog/lcb/lcb_v_strom_vector_radiator_grill_black_1.webp', 'images_processed/catalog/lcb/lcb_ktm390_radiator_grill.webp')
    ]

    for label, src, out_path in ktm_components:
        p = find_prod(None, label)
        if p and os.path.exists(src):
            if standardize_and_save(src, out_path):
                p['image'] = out_path
                p['gallery'] = [out_path]
                print(f"Fixed KTM ADV 390: {p['name']} -> {out_path}")
                fixed_count += 1

    # ==========================================
    # 5. RE-LINK VARIANTS FOR FIXED HELMETS
    # ==========================================
    print("\n--- Re-linking Multi-Color Variant Swatches for Fixed Helmets ---")
    
    # Link SBH-56 Vintage S1 family
    sbh56_ids = [
        'hrz-sbh-56-vintage-s1-glossy-blk-red-long-vis-helmet-2610',
        'hrz-sbh-56-vintage-s1-glossy-white-blk-long-vis-helmet-2612',
        'hrz-sbh-56-vintage-s1-glossy-blk-grey-long-vis-helmet-2614',
        'hrz-sbh-56-vintage-s1-glossy-white-red-long-vis-helmet-2620'
    ]
    sbh56_variants = []
    color_names = ['Glossy Black/Red', 'Glossy White/Black', 'Glossy Black/Grey', 'Glossy White/Red']
    for idx, pid in enumerate(sbh56_ids):
        prod = prod_map.get(pid)
        if prod:
            sbh56_variants.append({
                'id': prod['id'],
                'color': color_names[idx],
                'sku': prod.get('sku'),
                'price': prod.get('price'),
                'image': prod.get('image'),
                'gallery': prod.get('gallery', [prod.get('image')])
            })
    for pid in sbh56_ids:
        if pid in prod_map:
            prod_map[pid]['variants'] = sbh56_variants

    # Link SBH-25 family
    sbh25_ids = [
        'hrz-sbh-25-d-v-sharp-albus-glossy-black-red-helmet-2591',
        'hrz-sbh-25-d-v-sharp-albus-glossy-matt-blk-helmet-2593',
        'hrz-sbh-25-sharp-d-v-glossy-black-helmet-2604',
        'hrz-sbh-25-sharp-d-v-glossy-armada-blue-helmet-2618'
    ]
    sbh25_variants = []
    sbh25_colors = ['Albus Black/Red', 'Albus Matt/Black', 'Glossy Black', 'Armada Blue']
    for idx, pid in enumerate(sbh25_ids):
        prod = prod_map.get(pid)
        if prod:
            sbh25_variants.append({
                'id': prod['id'],
                'color': sbh25_colors[idx],
                'sku': prod.get('sku'),
                'price': prod.get('price'),
                'image': prod.get('image'),
                'gallery': prod.get('gallery', [prod.get('image')])
            })
    for pid in sbh25_ids:
        if pid in prod_map:
            prod_map[pid]['variants'] = sbh25_variants

    print(f"Total products updated and disentangled: {fixed_count}")

    # ==========================================
    # 6. WRITE OUT SYNCHRONIZED CATALOGS
    # ==========================================
    with open('data/products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    with open('test design site/data/products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print("\nSuccessfully synchronized data/products.json and test design site/data/products.json!")

    # Synchronize Final_Master_Catalogue_VERIFIED.xlsx
    try:
        import pandas as pd
        excel_path = 'Final_Master_Catalogue_VERIFIED.xlsx'
        df = pd.DataFrame(products)
        df.to_excel(excel_path, index=False)
        print("Successfully synchronized Final_Master_Catalogue_VERIFIED.xlsx!")
    except Exception as e:
        print(f"Note on excel export: {e}")

if __name__ == '__main__':
    run_fixes()
