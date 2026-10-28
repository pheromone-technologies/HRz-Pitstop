import glob
import os
from PIL import Image

def inspect_files(pattern):
    files = glob.glob(pattern, recursive=True)
    print(f"Pattern '{pattern}': found {len(files)} files")
    for f in sorted(files)[:20]:
        try:
            im = Image.open(f)
            print(f"  {f} | size: {im.size} | mode: {im.mode}")
        except Exception as e:
            print(f"  {f} | error: {e}")

print("=== Apache RTX 300 ===")
inspect_files("**/*apache_rtx_300*")

print("\n=== V Strom ===")
inspect_files("**/*v_strom*")

print("\n=== X Pulse ===")
inspect_files("**/*x_pulse*headlight*")
