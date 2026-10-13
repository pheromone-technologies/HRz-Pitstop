import requests
import os
import json

domains = {
    "ROYAL ENFIELD": "royalenfield.com",
    "YAMAHA": "yamaha-motor.com",
    "KTM": "ktm.com",
    "BAJAJ": "bajajauto.com",
    "HONDA": "honda.com",
    "SUZUKI": "globalsuzuki.com",
    "HERO": "heromotocorp.com",
    "TRIUMPH": "triumphmotorcycles.co.uk",
    "TVS": "tvsmotor.com",
    "HARLEY DAVIDSON": "harley-davidson.com"
}

os.makedirs(r'e:\coad\hrx website 2\images\brands', exist_ok=True)

for brand, domain in domains.items():
    url = f"https://logo.clearbit.com/{domain}"
    resp = requests.get(url)
    if resp.status_code == 200:
        with open(fr'e:\coad\hrx website 2\images\brands\{brand}.png', 'wb') as f:
            f.write(resp.content)
        print(f"Downloaded {brand}")
    else:
        print(f"Failed {brand}")
