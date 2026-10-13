import os
import requests
from rembg import remove

bikes_dir = r"e:\coad\hrx website 2\images\bikes"
os.makedirs(bikes_dir, exist_ok=True)

def normalize(name):
    return name.replace(" ", "_").replace("/", "_")

re_models = ["Scram 440 new", "Classic 650", "Bear 650", "Guerrilla 450", "Himalayan 450", "SUPER METEOR 650", "Hunter 350", "Himalayan", "Classic 350 Reborn", "Standard 350 Reborn", "Meteor 350", "Classic", "Standard", "Electra", "Interceptor", "Thunderbird", "Thunderbird X", "Continental GT", "Scram"]

def search_wikimedia(query):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": 3,
        "pithumbsize": 800
    }
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": "HRZ-Website-Builder/1.0"}, timeout=5).json()
        pages = resp.get("query", {}).get("pages", {})
        for pid, page in pages.items():
            if "thumbnail" in page:
                return page["thumbnail"]["source"]
    except Exception as e:
        print(f"Error fetching {query}: {e}")
    return None

for model in re_models:
    filename_base = "ROYAL_ENFIELD_" + normalize(model)
    jpg_path = os.path.join(bikes_dir, filename_base + ".jpg")
    png_path = os.path.join(bikes_dir, filename_base + "_transparent.png")
    
    query = f"Royal Enfield {model} motorcycle"
    print(f"Fetching {query}...")
    img_url = search_wikimedia(query)
    
    if img_url:
        try:
            print(f" -> Downloading {img_url}")
            img_data = requests.get(img_url, timeout=5).content
            
            # Save original jpg for the mapping reference
            with open(jpg_path, 'wb') as f:
                f.write(img_data)
                
            print(" -> Removing background...")
            transparent_data = remove(img_data)
            
            with open(png_path, 'wb') as f:
                f.write(transparent_data)
            print(" -> Done!")
        except Exception as e:
            print(f" -> Failed: {e}")
            
# Also get a logo
print("Fetching Royal Enfield Logo...")
logo_url = search_wikimedia("Royal Enfield logo")
if logo_url:
    try:
        img_data = requests.get(logo_url, timeout=5).content
        jpg_path = os.path.join(bikes_dir, "ROYAL_ENFIELD_logo.jpg")
        png_path = os.path.join(bikes_dir, "ROYAL_ENFIELD_logo_transparent.png")
        with open(jpg_path, 'wb') as f:
            f.write(img_data)
        transparent_data = remove(img_data)
        with open(png_path, 'wb') as f:
            f.write(transparent_data)
        print(" -> Logo Done!")
    except Exception as e:
        pass
