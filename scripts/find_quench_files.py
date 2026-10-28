import os

for root, dirs, files in os.walk('.'):
    if any(k in root for k in ['.git', '.venv']):
        continue
    for f in files:
        if 'quench' in f.lower():
            print(os.path.join(root, f))
