import hashlib
import glob
import os

files = [
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_aviator_saddle_stay_1.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_black_1.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_black_2.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_black_3.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_black_4.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_sliver_1.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_sliver_2.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_sliver_3.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_sliver_4.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vector_radiator_grill_black_1.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vector_radiator_grill_black_2.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vector_radiator_grill_black_3.webp',
    'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vector_radiator_grill_black_4.webp',
]

for f in files:
    if os.path.exists(f):
        h = hashlib.md5(open(f, 'rb').read()).hexdigest()
        size = os.path.getsize(f)
        print(f"{f}: size={size}, md5={h[:10]}")
    else:
        print(f"{f}: NOT FOUND")
