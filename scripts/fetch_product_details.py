import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0'}

handles = [
    'tvs-apache-rtx-300-vambrace-bashplate-silver',
    'tvs-apache-rtx-300-vambrace-bashplate-black-copy',
    'tvs-apache-rtx-300-vambrace-bashplate-silver-copy',
    'tvs-apache-rtx-300-vector-radiator-grill-black',
    'apache-rtx-300-vector-radiator-grill-silver',
    'legundary-v-strom-crash-guard-with-slider',
    'legundary-v-strom-vambrace-bash-plate',
    'x-pulse-200-4v-pro-cosmic-headlight-grill',
    'hero-x-pulse-headlight-grill',
    'tvs-apache-rtx-300-raptor-crash-guard-upper-lower-set-white',
    'tvs-apache-rtx-300-raptor-crash-guard-upper-lower-set-black',
]

for h in handles:
    url = f"https://www.legundary.com/products/{h}.json"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            prod = data.get('product', {})
            print(f"\n==========================================")
            print(f"Handle: {h}")
            print(f"Title: {prod.get('title')}")
            images = [img['src'] for img in prod.get('images', [])]
            print(f"Images ({len(images)}):")
            for i, img in enumerate(images):
                print(f"  [{i+1}] {img}")
    except Exception as e:
        print(f"Error for {h}: {e}")
