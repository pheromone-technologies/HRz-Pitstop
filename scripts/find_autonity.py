import json
import os

print("Searching for 'autonity' across json files:")
for root, dirs, files in os.walk('.'):
    if any(k in root for k in ['.git', '.venv']):
        continue
    for f in files:
        if f.endswith('.json'):
            full = os.path.join(root, f)
            try:
                with open(full, 'r', encoding='utf-8') as jf:
                    text = jf.read()
                    if 'autonity' in text.lower():
                        print(f"  Found in {full} (count: {text.lower().count('autonity')})")
            except Exception as e:
                pass
