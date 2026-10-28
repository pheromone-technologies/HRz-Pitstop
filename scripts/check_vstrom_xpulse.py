import hashlib
import glob
import os

check_list = [
    'images_processed/catalog/lcb/lcb_v_strom_adrinex_crash_guard_with_slider.webp',
    'images_processed/catalog/lcb/lcb_v_strom_adrinex_crash_guard_with_slider_1.webp',
    'images_processed/catalog/lcb/lcb_v_strom_adrinex_crash_guard_with_slider_2.webp',
    'images_processed/catalog/lcb/lcb_v_strom_adrinex_crash_guard_with_slider_3.webp',
    'images_processed/catalog/lcb/lcb_v_strom_adrinex_crash_guard_with_slider_4.webp',
    'images_processed/catalog/lcb/lcb_v_strom_vambrace_bashplate.webp',
    'images_processed/catalog/lcb/lcb_v_strom_vambrace_bashplate_1.webp',
    'images_processed/catalog/lcb/lcb_v_strom_vambrace_bashplate_2.webp',
    'images_processed/catalog/lcb/lcb_v_strom_vambrace_bashplate_3.webp',
    'images_processed/catalog/lcb/lcb_v_strom_vambrace_bashplate_4.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_200_4v_pro_cosmic_headlight_grill.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_200_4v_pro_cosmic_headlight_grill_1.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_200_4v_pro_cosmic_headlight_grill_2.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_200_4v_pro_cosmic_headlight_grill_3.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_200_4v_pro_cosmic_headlight_grill_4.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_headlight_grill.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_headlight_grill_1.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_headlight_grill_2.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_headlight_grill_3.webp',
    'images_processed/catalog/lcb/lcb_x_pulse_headlight_grill_4.webp',
]

for f in check_list:
    if os.path.exists(f):
        h = hashlib.md5(open(f, 'rb').read()).hexdigest()
        print(f"{f}: size={os.path.getsize(f)}, md5={h[:10]}")
    else:
        print(f"{f}: NOT FOUND")
