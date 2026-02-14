"""
Dataset Cleaning Script.
Removes mislabeled samples based on audit findings.
"""
import json
import re

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"

# Patterns that indicate GAMING context (not criminal hacking)
GAMING_PATTERNS = [
    re.compile(r"كلاش|clash", re.I),
    re.compile(r"ماين كرافت|minecraft", re.I),
    re.compile(r"ببجي|pubg", re.I),
    re.compile(r"فورت|fortnite", re.I),
    re.compile(r"فري فاير", re.I),
    re.compile(r"سيرفر.*ماين|سيرفر.*نص قلب", re.I),
    re.compile(r"مود.*كشف|اكس راي", re.I),
    re.compile(r"بوت.*تيك توك.*رشق", re.I),
]

# Patterns that indicate REAL hacking (keep these)
REAL_HACKING_PATTERNS = [
    re.compile(r"اختراق.*حساب", re.I),
    re.compile(r"تجسس.*واتس|تجسس.*سناب", re.I),
    re.compile(r"سرقة.*حساب", re.I),
    re.compile(r"استرجاع.*حسابات", re.I),
]

def clean_dataset():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data)
    cleaned_data = []
    removed = {"Hacking (gaming)": 0, "Spam (short)": 0, "Other": 0}
    
    for d in data:
        text = d['text']
        label = d['label']
        keep = True
        
        # Clean Hacking: Remove gaming context
        if label == "Hacking":
            is_gaming = any(p.search(text) for p in GAMING_PATTERNS)
            is_real = any(p.search(text) for p in REAL_HACKING_PATTERNS)
            
            if is_gaming and not is_real:
                keep = False
                removed["Hacking (gaming)"] += 1
        
        # Clean Spam: Remove too short samples
        if label == "Spam" and len(text) < 40:
            keep = False
            removed["Spam (short)"] += 1
        
        if keep:
            cleaned_data.append(d)
    
    # Save cleaned data
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
    
    print(f"Original: {original_count} samples")
    print(f"Cleaned: {len(cleaned_data)} samples")
    print(f"Removed: {original_count - len(cleaned_data)}")
    print("Breakdown:", removed)

if __name__ == "__main__":
    clean_dataset()
