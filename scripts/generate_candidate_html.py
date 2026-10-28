import os

html = ['<!DOCTYPE html><html><head><style>',
        'body { background: #111; color: #eee; font-family: sans-serif; padding: 20px; }',
        '.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }',
        '.card { background: #222; border-radius: 8px; padding: 10px; text-align: center; }',
        '.card img { max-width: 100%; height: 260px; object-fit: contain; background: #333; border-radius: 4px; }',
        '.card p { margin: 8px 0 0; font-size: 13px; word-break: break-all; }',
        '</style></head><body><h1>Candidates Gallery</h1><div class="grid">']

for f in sorted(os.listdir('scratch/image_candidates')):
    if not f.endswith(('.webp', '.jpg', '.png')): continue
    html.append(f'<div class="card"><img src="{f}"><p>{f}</p></div>')

html.append('</div></body></html>')

with open('scratch/image_candidates/index.html', 'w', encoding='utf-8') as out:
    out.write('\n'.join(html))
print("Wrote scratch/image_candidates/index.html")
