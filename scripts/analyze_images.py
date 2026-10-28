import os
from PIL import Image
import numpy as np

def analyze_img(path):
    if not os.path.exists(path):
        return "NOT_EXISTS"
    im = Image.open(path)
    w, h = im.size
    mode = im.mode
    arr = np.array(im.convert('RGB'))
    # Check if border is pure black or dark (pillarbox)
    left_col = arr[:, :15, :]
    right_col = arr[:, -15:, :]
    left_dark = np.mean(left_col)
    right_dark = np.mean(right_col)
    center = arr[h//4:3*h//4, w//4:3*w//4, :]
    center_bright = np.mean(center)
    return f"size={w}x{h}, mode={mode}, left_mean={left_dark:.1f}, right_mean={right_dark:.1f}, center_mean={center_bright:.1f}"

files = [
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

for f in files:
    print(f"{os.path.basename(f)}: {analyze_img(f)}")
