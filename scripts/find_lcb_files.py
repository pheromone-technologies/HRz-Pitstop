import glob
import os

print("=== Catalog LCB Apache RTX 300 ===")
for f in sorted(glob.glob("images_processed/catalog/lcb/*apache_rtx_300*")):
    print(f)

print("\n=== Scraped LCB Apache RTX 300 ===")
for f in sorted(glob.glob("images_processed/scraped/lcb/*APACHE_RTX*")):
    print(f)

print("\n=== All Scraped LCB Vambrace ===")
for f in sorted(glob.glob("images_processed/scraped/lcb/*VAMBRACE*")):
    print(f)

print("\n=== All Scraped LCB Vector Radiator ===")
for f in sorted(glob.glob("images_processed/scraped/lcb/*VECTOR_RADIATOR*")):
    print(f)
