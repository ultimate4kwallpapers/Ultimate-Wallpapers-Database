import os
import json
import requests
from PIL import Image

# Hugging Face Free AI Model
API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
HF_TOKEN = os.environ.get("HF_TOKEN")
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Aapke 4 Folders
FOLDERS = {
    "anime": "anime_popular",
    "animeLive": "anime_live",
    "other": "other_popular",
    "otherLive": "other_live"
}

repo_name = os.environ.get('GITHUB_REPOSITORY', 'ultimate4kwallpapers/Ultimate-Wallpapers-Database')
BASE_URL = f"https://raw.githubusercontent.com/{repo_name}/main/"

def get_fallback_tags(filename):
    # Agar AI fail ho jaye, toh image ke naam se tags nikalega (e.g. naruto_red.jpg -> naruto, red)
    name_without_ext = os.path.splitext(filename)[0]
    return name_without_ext.lower().replace("-", "_").split('_')

def get_ai_tags(image_path, filename):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
            
        response = requests.post(API_URL, headers=headers, data=data)
        
        # Agar Hugging Face ne error diya (limit cross ho gayi) toh naam (fallback) se tags nikal lo
        if response.status_code != 200:
            print(f"AI Limit reached ya Error aaya. Image ke naam se tags nikal raha hu: {filename}")
            return get_fallback_tags(filename)
            
        result = response.json()
        caption = result[0]['generated_text'].lower()
        
        ignore_words = ['a', 'an', 'the', 'with', 'and', 'in', 'on', 'of', 'to', 'is', 'character', 'picture', 'image', 'background', 'showing']
        raw_tags = caption.split()
        
        clean_tags = []
        for word in raw_tags:
            word = word.replace(',', '').replace('.', '')
            if word not in ignore_words and len(word) > 2:
                clean_tags.append(word)
                
        # Folder ke hisaab se default tag lagana
        if "anime" in image_path.lower():
            clean_tags.append("anime")
            
        return list(set(clean_tags))
        
    except Exception as e:
        print(f"AI Tagging failed. Fallback to name for {filename}")
        return get_fallback_tags(filename)

def get_dominant_color(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((1, 1), resample=0)
        return '#%02x%02x%02x' % img.getpixel((0, 0))
    except:
        return "#1f1f1f"

def get_aspect_ratio(image_path):
    try:
        img = Image.open(image_path)
        from fractions import Fraction
        f = Fraction(img.size[0], img.size[1]).limit_denominator(100)
        return f"{f.numerator}/{f.denominator}"
    except:
        return "9/16"

def generate_data():
    data = {"anime": [], "other": [], "animeLive": [], "otherLive": []}
    
    for key, folder in FOLDERS.items():
        if not os.path.exists(folder):
            continue
            
        for filename in os.listdir(folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.mp4')):
                file_path = os.path.join(folder, filename)
                url = BASE_URL + file_path.replace("\\", "/")
                
                item = {"url": url}
                
                if not filename.lower().endswith('.mp4'):
                    item["tags"] = get_ai_tags(file_path, filename)
                    item["ratio"] = get_aspect_ratio(file_path)
                    item["color"] = get_dominant_color(file_path)
                else:
                    item["tags"] = ["live", "wallpaper"] + get_fallback_tags(filename)
                    item["ratio"] = "9/16"
                    item["color"] = "#111111"
                    
                data[key].append(item)
                
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Mubarak ho! Saara data JSON me save ho gaya!")

if __name__ == "__main__":
    generate_data()
          
