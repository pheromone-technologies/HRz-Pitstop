import os
import glob
from PIL import Image

def summarize_img(f):
    if not os.path.exists(f): return "MISSING"
    im = Image.open(f)
    return f"{im.size}, mode={im.mode}"

print("=== V STROM ADRINEX CRASH GUARD ===")
for i in ["", "_1", "_2", "_3", "_4"]:
    f = f"images_processed/catalog/lcb/lcb_v_strom_adrinex_crash_guard_with_slider{i}.webp"
    print(f"  {i or 'base'}: {summarize_img(f)}")

print("\n=== V STROM VAMBRACE BASHPLATE ===")
for i in ["", "_1", "_2", "_3", "_4"]:
    f = f"images_processed/catalog/lcb/lcb_v_strom_vambrace_bashplate{i}.webp"
    print(f"  {i or 'base'}: {summarize_img(f)}")

print("\n=== X PULSE HEADLIGHT GRILL ===")
for i in ["", "_1", "_2", "_3", "_4"]:
    f = f"images_processed/catalog/lcb/lcb_x_pulse_headlight_grill{i}.webp"
    print(f"  {i or 'base'}: {summarize_img(f)}")
