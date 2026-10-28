from PIL import Image
import os

LOGO_FILE = r"E:\coad\tools for hrz\image logo editor\HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.png"
HRZ_LOGO = Image.open(LOGO_FILE).convert('RGBA')

raw_path = "images_processed/scraped/lcb/LCB_RE_GUERRILLA_450_BAZOOKA_CRASH_GUARD_937922.webp"
target_path = "images_processed/catalog/lcb/lcb_re_guerrilla_450_bazooka_crash_guard.webp"

raw_im = Image.open(raw_path).convert('RGBA')
w, h = raw_im.size

scale_factor = 0.15
padding = max(15, int(w * 0.02))

wm_w = int(w * scale_factor)
wm_ratio = wm_w / float(HRZ_LOGO.width)
wm_h = int(HRZ_LOGO.height * wm_ratio)
resized_logo = HRZ_LOGO.resize((wm_w, wm_h), Image.Resampling.LANCZOS)

x = w - wm_w - padding
y = h - wm_h - padding
raw_im.alpha_composite(resized_logo, dest=(x, y))

final_rgb = raw_im.convert('RGB')
final_rgb.save(target_path, 'WEBP', quality=88)
print(f"Successfully updated {target_path} from raw {raw_path}")
