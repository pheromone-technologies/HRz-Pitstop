import os

print("Files in images/:")
for root, dirs, files in os.walk('images'):
    for f in files:
        full = os.path.join(root, f)
        print(f"  {full} ({os.path.getsize(full)} bytes)")
