import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'<script\s+(?!.*?defer\b)([^>]*src=["\']js/[^"\']+["\'][^>]*)>', r'<script defer \1>', content)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added defer to scripts in index.html")
