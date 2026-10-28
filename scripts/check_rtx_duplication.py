import hashlib
import glob

hashes = {}
for f in sorted(glob.glob("images_processed/catalog/lcb/*apache_rtx_300*")):
    h = hashlib.md5(open(f, 'rb').read()).hexdigest()
    hashes.setdefault(h, []).append(f)

for h, flist in hashes.items():
    print(f"Hash {h[:10]} ({len(flist)} files):")
    for f in flist:
        print(f"   {f}")
