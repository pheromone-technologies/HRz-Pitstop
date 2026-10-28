import os
from PIL import Image
import numpy as np

for name in ['lcb_v_strom_adrinex_crash_guard_with_slider', 'lcb_v_strom_vambrace_bashplate', 'lcb_x_pulse_headlight_grill']:
    print(f"\n=== {name} ===")
    for suffix in ['', '_1', '_2', '_3', '_4']:
        p = f"images_processed/catalog/lcb/{name}{suffix}.webp"
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert('RGB')
        arr = np.array(im)
        # Check white background percentage (pixels with R>240, G>240, B>240)
        white_mask = (arr[:, :, 0] > 240) & (arr[:, :, 1] > 240) & (arr[:, :, 2] > 240)
        white_pct = np.mean(white_mask) * 100
        # Check dark pixels (product)
        dark_mask = (arr[:, :, 0] < 80) & (arr[:, :, 1] < 80) & (arr[:, :, 2] < 80)
        dark_pct = np.mean(dark_mask) * 100
        print(f"  {suffix or 'base'}: size={im.size}, white={white_pct:.1f}%, dark={dark_pct:.1f}%")
